import datetime
import logging
from typing import Optional, Dict, List, Any

from src.database.connection import get_connection

logger = logging.getLogger(__name__)


def _ph(conn) -> str:
    """Retorna el placeholder correcto segun el driver: ? para SQLite, %s para Postgres/MySQL."""
    try:
        module = type(conn).__module__
        if "sqlite" in module:
            return "?"
        return "%s"
    except Exception:
        return "?"


def _table_exists(conn, table_name: str) -> bool:
    """Helper: verifica si tabla existe."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cur.fetchone() is not None
    except Exception:
        return False


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    """Helper: verifica si columna existe en tabla."""
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        cols = [r[1] for r in cur.fetchall()]
        return column_name in cols
    except Exception:
        return False


def ensure_schema() -> None:
    """Verifica y agrega columnas faltantes en tablas POS (migrations only).
    
    Las tablas principales (cash_sessions, cash_movements) se crean en 
    src.database.connection.init_db(). Esta función solo agrega columnas 
    que podrían faltar en bases de datos antiguas o migraciones incompletas.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            # Migration: agregar columnas a cash_sessions si faltan
            if _table_exists(conn, 'cash_sessions'):
                if not _column_exists(conn, 'cash_sessions', 'arqueo_declared'):
                    try:
                        cur.execute("ALTER TABLE cash_sessions ADD COLUMN arqueo_declared REAL")
                    except Exception:
                        pass
                if not _column_exists(conn, 'cash_sessions', 'arqueo_notes'):
                    try:
                        cur.execute("ALTER TABLE cash_sessions ADD COLUMN arqueo_notes TEXT")
                    except Exception:
                        pass
                    
            # Migration: agregar columnas a cash_movements si faltan
            if _table_exists(conn, 'cash_movements'):
                if not _column_exists(conn, 'cash_movements', 'description'):
                    try:
                        cur.execute("ALTER TABLE cash_movements ADD COLUMN description TEXT")
                    except Exception:
                        pass
            
            conn.commit()
        except Exception as e:
            logger.error("ensure_schema (POS): %s", e)


def get_current_session(user_id: int) -> Optional[Dict[str, Any]]:
    """Devuelve la sesion de caja abierta actual del usuario si existe."""
    with get_connection() as conn:
        p = _ph(conn)
        cur = conn.cursor()
        cur.execute(
            f"SELECT id, user_id, opening_amount, closing_amount, opened_at, closed_at "
            f"FROM cash_sessions WHERE user_id = {p} AND closed_at IS NULL "
            f"ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id":             row[0],
            "user_id":        row[1],
            "opening_amount": row[2],
            "closing_amount": row[3],
            "opened_at":      row[4],
            "closed_at":      row[5],
        }


def open_cash_session(user_id: int, opening_amount: float) -> int:
    """Abre una nueva sesion de caja. Retorna el ID de la sesion."""
    if opening_amount < 0:
        raise ValueError("El monto de apertura no puede ser negativo.")
    current = get_current_session(user_id)
    if current:
        raise ValueError("Ya existe una sesion de caja abierta.")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        p = _ph(conn)
        cur = conn.cursor()
        try:
            cur.execute(
                f"INSERT INTO cash_sessions (user_id, opening_amount, opened_at) VALUES ({p},{p},{p})",
                (user_id, float(opening_amount), now)
            )
            conn.commit()
            return cur.lastrowid
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error("open_cash_session: %s", e)
            raise


def close_cash_session(session_id: int, closing_amount: float) -> Dict[str, Any]:
    """Cierra la sesion de caja. Retorna resumen final para el arqueo."""
    if closing_amount < 0:
        raise ValueError("El monto de cierre no puede ser negativo.")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        p = _ph(conn)
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT closed_at FROM cash_sessions WHERE id = {p}", (session_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("La sesion de caja no existe.")
            if row[0] is not None:
                raise ValueError("La sesion de caja ya esta cerrada.")
            cur.execute(
                f"UPDATE cash_sessions SET closing_amount = {p}, closed_at = {p} WHERE id = {p}",
                (float(closing_amount), now, session_id)
            )
            conn.commit()
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error("close_cash_session: %s", e)
            raise
    return get_session_summary(session_id)


def register_cash_movement(session_id: int, mov_type: str, amount: float, description: str = "") -> int:
    """Registra un movimiento en caja (sale, expense, withdrawal).
    FIX: verifica que la sesion este abierta.
    FIX: acepta 'description' para identificar movimientos en el arqueo.
    """
    VALID = ("sale", "expense", "withdrawal")
    if mov_type not in VALID:
        raise ValueError(f"Tipo '{mov_type}' invalido. Use: {VALID}")
    if amount < 0:
        raise ValueError("El monto no puede ser negativo.")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        p = _ph(conn)
        cur = conn.cursor()
        # FIX: verificar sesion abierta
        cur.execute(f"SELECT closed_at FROM cash_sessions WHERE id = {p}", (session_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Sesion de caja no encontrada.")
        if row[0] is not None:
            raise ValueError("No se puede registrar movimiento en sesion cerrada.")
        try:
            cur.execute(
                f"INSERT INTO cash_movements (session_id, type, amount, description, created_at) "
                f"VALUES ({p},{p},{p},{p},{p})",
                (session_id, mov_type, float(amount), description or "", now)
            )
            conn.commit()
            return cur.lastrowid
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error("register_cash_movement: %s", e)
            raise


def get_session_summary(session_id: int) -> Dict[str, Any]:
    """Resumen completo de la sesion: apertura, ventas, gastos, retiros, diferencia.

    También retorna el valor declarado en el arqueo (arqueo_declared) si existe.
    """
    with get_connection() as conn:
        p = _ph(conn)
        cur = conn.cursor()
        cur.execute(
            f"SELECT opening_amount, closing_amount, opened_at, closed_at, arqueo_declared "
            f"FROM cash_sessions WHERE id = {p}",
            (session_id,)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Sesion no encontrada.")
        opening, closing_amount, opened_at, closed_at, arqueo_declared = row
        cur.execute(
            f"SELECT type, SUM(amount) FROM cash_movements WHERE session_id = {p} GROUP BY type",
            (session_id,)
        )
        totals      = {r[0]: (r[1] or 0.0) for r in cur.fetchall()}
        sales       = totals.get("sale", 0.0)
        expenses    = totals.get("expense", 0.0)
        withdrawals = totals.get("withdrawal", 0.0)
        expected    = opening + sales - expenses - withdrawals
        difference  = (closing_amount - expected) if closing_amount is not None else None
        return {
            "session_id":       session_id,
            "opening":          opening,
            "sales":            sales,
            "expenses":         expenses,
            "withdrawals":      withdrawals,
            "expected_closing": expected,
            "closing_amount":   closing_amount,
            "difference":       difference,
            "opened_at":        opened_at,
            "closed_at":        closed_at,
            "arqueo_declared":  arqueo_declared,
        }


def list_movements(session_id: int) -> List[Dict[str, Any]]:
    """Lista todos los movimientos de una sesion con nota y timestamp."""
    with get_connection() as conn:
        p = _ph(conn)
        cur = conn.cursor()
        cur.execute(
            f"SELECT id, type, amount, description, created_at "
            f"FROM cash_movements WHERE session_id = {p} ORDER BY id ASC",
            (session_id,)
        )
        return [
            {"id": r[0], "type": r[1], "amount": r[2], "description": r[3] or "", "created_at": r[4]}
            for r in cur.fetchall()
        ]


# additional helpers for cash manager window and tests

def get_session_history(from_date: str = None, to_date: str = None, user_id: int = None) -> List[Dict[str, Any]]:
    """Devuelve lista de sesiones con resumen, opcionalmente filtradas por rango de fechas o usuario."""
    with get_connection() as conn:
        p = _ph(conn)
        cur = conn.cursor()
        sql = "SELECT id FROM cash_sessions WHERE 1=1"
        params: list = []
        if from_date:
            sql += f" AND opened_at >= {p}"
            params.append(from_date)
        if to_date:
            sql += f" AND opened_at <= {p}"
            params.append(to_date)
        if user_id:
            sql += f" AND user_id = {p}"
            params.append(user_id)
        sql += " ORDER BY opened_at DESC"
        cur.execute(sql, params)
        rows = cur.fetchall()
        history = []
        for r in rows:
            sid = r[0]
            try:
                summary = get_session_summary(sid)
            except Exception:
                continue
            estado = "abierta" if summary.get("closed_at") is None else "cerrada"
            summary["estado"] = estado
            history.append(summary)
        return history


def get_session_detail(session_id: int) -> List[Dict[str, Any]]:
    """Retorna movimientos detallados de una sesion."""
    return list_movements(session_id)


def save_arqueo(session_id: int, declared_amount: float, notes: str = "") -> None:
    """Guarda el monto declarado por el cajero sin cerrar la sesión."""
    with get_connection() as conn:
        p = _ph(conn)
        cur = conn.cursor()
        try:
            cur.execute(
                f"UPDATE cash_sessions SET arqueo_declared = {p}, arqueo_notes = {p} WHERE id = {p}",
                (float(declared_amount), notes, session_id)
            )
            conn.commit()
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error("save_arqueo: %s", e)
            raise
