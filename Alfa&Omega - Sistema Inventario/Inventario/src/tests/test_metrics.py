"""Tests for metrics logging."""
import sys
from pathlib import Path

# ensure project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core import metrics


def teardown_module(module):
    try:
        if metrics.METRICS_FILE.exists():
            metrics.METRICS_FILE.unlink()
    except Exception:
        pass


def test_record_and_increment():
    metrics.increment("sales", 2)
    metrics.record("test_event", {"foo": "bar"})
    assert metrics.METRICS_FILE.exists()
    text = metrics.METRICS_FILE.read_text()
    assert "sales" in text
    assert "test_event" in text


def test_error():
    metrics.error("Something failed")
    text = metrics.METRICS_FILE.read_text()
    assert "Something failed" in text


def test_concurrent_writes(tmp_path):
    # simulate rapid threads incrementing same key
    from threading import Thread
    metrics.METRICS_FILE.unlink(missing_ok=True)
    def worker():
        for _ in range(10):
            metrics.increment("concurrent", 1)
    threads = [Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    content = metrics.METRICS_FILE.read_text()
    assert "concurrent" in content


if __name__ == "__main__":
    test_record_and_increment()
    test_error()
    print("metrics tests passed")