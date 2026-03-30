from datetime import datetime, timedelta
import importlib

# pos_service must be reloaded when the temporary DB path changes (use_temp_db fixture)
import src.services.pos_service as pos_service
from src.database.connection import get_connection


def setup_function(fn):
    # reload configuration and connection modules so that new DB_PATH is picked up
    import config.settings as cfg
    import src.database.connection as dbconn
    importlib.reload(cfg)
    importlib.reload(dbconn)
    # now reload pos_service so its imported get_connection is fresh
    importlib.reload(pos_service)


def test_open_close_session():
    # debug information
    from src.database import connection as dbconn
    print("debug DB_PATH=", dbconn.DB_PATH)
    with dbconn.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM cash_sessions")
        print("existing sessions at start", cur.fetchall())
    pos_service.ensure_schema()
    user_id = 1
    sid = pos_service.open_cash_session(user_id, 100.0)
    assert sid is not None
    summary = pos_service.get_session_summary(sid)
    assert summary["opening"] == 100.0
    # cerrar
    res = pos_service.close_cash_session(sid, 150.0)
    assert res["closing_amount"] == 150.0
    assert pos_service.get_current_session(user_id) is None


def test_manual_movement_ingreso():
    pos_service.ensure_schema()
    user_id = 2
    sid = pos_service.open_cash_session(user_id, 50.0)
    pos_service.register_cash_movement(sid, "sale", 10.0, "test ingreso")
    detail = pos_service.get_session_detail(sid)
    assert any(d["type"] == "sale" for d in detail)


def test_manual_movement_egreso():
    pos_service.ensure_schema()
    user_id = 3
    sid = pos_service.open_cash_session(user_id, 50.0)
    pos_service.register_cash_movement(sid, "expense", 5.0, "test egreso")
    detail = pos_service.get_session_detail(sid)
    assert any(d["type"] == "expense" for d in detail)


def test_arqueo_con_diferencia():
    pos_service.ensure_schema()
    user_id = 4
    sid = pos_service.open_cash_session(user_id, 20.0)
    pos_service.register_cash_movement(sid, "sale", 10.0)
    # save arqueo con monto distinto al esperado
    pos_service.save_arqueo(sid, declared_amount=25.0, notes="chequeo")
    summary = pos_service.get_session_summary(sid)
    assert summary.get("arqueo_declared") == 25.0
    expected = summary["opening"] + summary["sales"] - summary["expenses"] - summary["withdrawals"]
    assert abs(25.0 - expected) > 0.001


def test_historial_filtrado_por_fecha():
    pos_service.ensure_schema()
    user_id = 5
    # primera sesion (ayer)
    sid1 = pos_service.open_cash_session(user_id, 10.0)
    pos_service.close_cash_session(sid1, 10.0)
    yesterday = datetime.now() - timedelta(days=1)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE cash_sessions SET opened_at=? WHERE id=?", (yesterday.strftime("%Y-%m-%d %H:%M:%S"), sid1))
        conn.commit()
    # segunda sesion (hoy)
    sid2 = pos_service.open_cash_session(user_id, 20.0)
    pos_service.close_cash_session(sid2, 20.0)

    frm = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hist = pos_service.get_session_history(from_date=frm)
    ids = [h["session_id"] for h in hist]
    assert sid2 in ids
    assert sid1 not in ids
