"""
src/services/prediccion.py
===========================
Tarea 20 — Predicción de demanda con Holt-Winters.
Si statsmodels no disponible → fallback promedio móvil.
Columnas reales kardex_moves: type, date, qty, product_code.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from src.database.connection import get_connection

_LOG = logging.getLogger(__name__)

_ALERTA_CRITICO = 3    # días
_ALERTA_BAJO    = 10   # días


def get_ventas_diarias(codigo: str, dias: int = 90) -> List[Dict[str, Any]]:
    """
    Retorna lista de {fecha: str, qty_vendida: float} para los últimos `dias` días.
    Solo movimientos type='OUT' del producto.
    """
    desde = (date.today() - timedelta(days=dias)).isoformat()
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT DATE(date) AS dia, SUM(qty) AS total
                FROM kardex_moves
                WHERE product_code = ?
                  AND type = 'OUT'
                  AND DATE(date) >= ?
                GROUP BY dia
                ORDER BY dia ASC
                """,
                (codigo, desde),
            )
            return [{"fecha": r[0], "qty_vendida": float(r[1])} for r in cur.fetchall()]
    except Exception as e:
        logging.warning("get_ventas_diarias(%r) error: %s", codigo, e)
        return []


def _fallback_promedio(ventas: List[Dict], dias_futuro: int) -> List[Dict[str, Any]]:
    """Predicción simple: promedio de últimos 14 días como constante."""
    if not ventas:
        return []
    vals = [v["qty_vendida"] for v in ventas[-14:]]
    avg = sum(vals) / len(vals)
    hoy = date.today()
    return [
        {"fecha": (hoy + timedelta(days=i + 1)).isoformat(), "qty_predicha": round(avg, 2)}
        for i in range(dias_futuro)
    ]


def _get_nombre_y_stock(codigo: str):
    """Retorna (nombre, cantidad) del producto o (codigo, 0)."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT nombre, cantidad FROM productos WHERE codigo = ?", (codigo,)
            )
            row = cur.fetchone()
            if row:
                return row[0], int(row[1] or 0)
    except Exception as e:
        logging.warning("_get_nombre_y_stock(%r): %s", codigo, e)
    return codigo, 0


def predecir_demanda(codigo: str, dias_futuro: int = 30) -> Dict[str, Any]:
    """
    Predice la demanda futura de un producto.
    Usa Holt-Winters (ExponentialSmoothing) con fallback a promedio móvil.
    """
    nombre, stock_actual = _get_nombre_y_stock(codigo)
    ventas = get_ventas_diarias(codigo, dias=90)

    if len(ventas) < 14:
        return {"error": "datos_insuficientes", "codigo": codigo, "nombre": nombre,
                "stock_actual": stock_actual, "dias_datos": len(ventas)}

    # Intentar Holt-Winters
    prediccion: List[Dict[str, Any]] = []
    metodo = "fallback"
    try:
        import pandas as pd
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        # Serie de tiempo diaria (rellenar días sin ventas con 0)
        df = pd.DataFrame(ventas).set_index("fecha")
        df.index = pd.to_datetime(df.index)
        df = df.reindex(
            pd.date_range(df.index.min(), date.today().isoformat(), freq="D"), fill_value=0.0
        )
        serie = df["qty_vendida"].astype(float)

        if len(serie) >= 14:
            modelo = ExponentialSmoothing(serie, trend="add", seasonal=None).fit(
                optimized=True, use_brute=False
            )
            forecast = modelo.forecast(dias_futuro)
            prediccion = [
                {"fecha": str(f.date()), "qty_predicha": max(0.0, round(float(v), 2))}
                for f, v in zip(forecast.index, forecast.values)
            ]
            metodo = "holt_winters"
    except Exception as e:
        logging.warning("Holt-Winters falló para %r: %s — usando fallback", codigo, e)
        prediccion = _fallback_promedio(ventas, dias_futuro)

    if not prediccion:
        prediccion = _fallback_promedio(ventas, dias_futuro)

    # KPIs
    total_vendido = sum(v["qty_vendida"] for v in ventas)
    dias_con_datos = len(ventas)
    promedio_diario = round(total_vendido / max(dias_con_datos, 1), 2)

    fecha_quiebre: Optional[str] = None
    if promedio_diario > 0:
        dias_cobertura = int(stock_actual / promedio_diario)
        if dias_cobertura < 365:
            fecha_quiebre = (date.today() + timedelta(days=dias_cobertura)).isoformat()
    else:
        dias_cobertura = 9999

    if dias_cobertura <= _ALERTA_CRITICO:
        alerta = "CRITICO"
    elif dias_cobertura <= _ALERTA_BAJO:
        alerta = "BAJO"
    else:
        alerta = "OK"

    return {
        "codigo":          codigo,
        "nombre":          nombre,
        "stock_actual":    stock_actual,
        "promedio_diario": promedio_diario,
        "dias_cobertura":  dias_cobertura,
        "alerta":          alerta,
        "prediccion":      prediccion,
        "fecha_quiebre":   fecha_quiebre,
        "metodo":          metodo,
    }


def get_resumen_predicciones() -> List[Dict[str, Any]]:
    """
    Corre predecir_demanda() para todos los productos con ventas en 90d.
    Retorna: codigo, nombre, stock_actual, dias_cobertura, alerta, fecha_quiebre.
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            desde = (date.today() - timedelta(days=90)).isoformat()
            cur.execute(
                """
                SELECT DISTINCT product_code FROM kardex_moves
                WHERE type = 'OUT' AND DATE(date) >= ?
                """,
                (desde,),
            )
            codigos = [r[0] for r in cur.fetchall()]
    except Exception as e:
        logging.warning("get_resumen_predicciones error: %s", e)
        return []

    resultados = []
    for codigo in codigos:
        r = predecir_demanda(codigo)
        if "error" not in r:
            resultados.append({
                "codigo":         r["codigo"],
                "nombre":         r["nombre"],
                "stock_actual":   r["stock_actual"],
                "dias_cobertura": r["dias_cobertura"],
                "alerta":         r["alerta"],
                "fecha_quiebre":  r.get("fecha_quiebre"),
            })

    resultados.sort(key=lambda x: x["dias_cobertura"])
    return resultados
