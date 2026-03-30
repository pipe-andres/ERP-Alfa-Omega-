"""Tests for the update_manager module."""
import sys
from pathlib import Path
import json

# ensure project path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core import update_manager

def test_local_version():
    v = update_manager.get_local_version()
    assert v == "3.5.0"


def test_remote_version_file(tmp_path):
    data = {"version": "4.0.0", "release_date": "", "notes": ""}
    f = tmp_path / "remote.json"
    f.write_text(json.dumps(data))
    info = update_manager.get_remote_version(str(f))
    assert info["version"] == "4.0.0"
    assert update_manager.is_update_available(info)


def test_no_update_available(tmp_path):
    data = {"version": "0.9.0"}
    f = tmp_path / "remote.json"
    f.write_text(json.dumps(data))
    info = update_manager.get_remote_version(str(f))
    assert not update_manager.is_update_available(info)


def test_equal_versions(tmp_path):
    data = {"version": "3.5.0"}
    f = tmp_path / "remote.json"
    f.write_text(json.dumps(data))
    info = update_manager.get_remote_version(str(f))
    assert not update_manager.is_update_available(info)


def test_remote_fetch_missing_requests(monkeypatch, tmp_path):
    # simulate absence of requests module
    monkeypatch.setitem(sys.modules, 'requests', None)
    # calling get_remote_version with an http URL should return None (silent, not raise)
    result = update_manager.get_remote_version('http://nonexistent')
    assert result is None


def test_download_update_failure(monkeypatch, tmp_path):
    # simulate download returning error status using a stub object
    # (cannot patch None.get, so we inject a stub with a .get method)
    import types
    class DummyResp:
        status_code = 404
        def iter_content(self, chunk_size):
            yield b''
        def raise_for_status(self):
            raise Exception("404")
    stub = types.SimpleNamespace(get=lambda *a, **kw: DummyResp())
    monkeypatch.setattr(update_manager, 'requests', stub)
    # ensure it handles gracefully without raising
    result = update_manager.download_update('http://fake', tmp_path / 'out.exe')
    assert result is False

if __name__ == "__main__":
    test_local_version()
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as td:
        p = Path(td)
        test_remote_version_file(p)
        test_no_update_available(p)
    print("update tests passed")
