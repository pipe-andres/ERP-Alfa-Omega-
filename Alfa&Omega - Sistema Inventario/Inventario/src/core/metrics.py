"""Registro de métricas del sistema.
Guarda entradas en logs/metrics.log con formato simple.
"""
from datetime import datetime, timezone
from pathlib import Path
import threading

METRICS_FILE = Path(__file__).parent.parent.parent / "logs" / "metrics.log"
_METRICS_LOCK = threading.Lock()


def _write(line: str):
    METRICS_FILE.parent.mkdir(exist_ok=True)
    with _METRICS_LOCK:
        with open(METRICS_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def record(event: str, data: dict = None) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    entry = {"ts": ts, "event": event, "data": data or {}}
    _write(str(entry))


def increment(counter: str, amount: int = 1) -> None:
    record("counter", {"name": counter, "inc": amount})


def error(err_msg: str) -> None:
    record("error", {"msg": err_msg})
