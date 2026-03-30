"""Tests for the system_info helper used by the GUI."""
import sys
from pathlib import Path
import datetime

# ensure project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core import system_info, license_manager, update_manager
from config import settings


def teardown_module(module):
    # clean up any files we touched
    try:
        if license_manager.LICENSE_FILE.exists():
            license_manager.LICENSE_FILE.unlink()
    except Exception:
        pass
    try:
        f = settings.LOG_DIR / "sistema.log"
        if f.exists():
            f.unlink()
    except Exception:
        pass
    try:
        for p in settings.BACKUP_DIR.glob("*.db"):
            p.unlink()
    except Exception:
        pass


def test_empty_state(tmp_path, monkeypatch):
    # Patch system_info to read logs from a clean tmp directory
    # so test_populated_state run order cannot pollute this test
    from config import settings as _settings
    monkeypatch.setattr(_settings, 'LOG_DIR', tmp_path)
    monkeypatch.setattr(_settings, 'BACKUP_DIR', tmp_path / 'bkp')
    (tmp_path / 'bkp').mkdir()

    # Remove license to test empty-license scenario
    try:
        license_manager.LICENSE_FILE.unlink()
    except Exception:
        pass

    info = system_info.get_system_info()
    assert info["license_valid"] is False
    assert isinstance(info["local_version"], str)
    assert info["backup_count"] == 0
    assert info["recent_logs"] in ("", "(no disponible)")


def test_populated_state(tmp_path, monkeypatch):
    from config import settings as _settings
    log_dir = tmp_path / "logs"
    backup_dir = tmp_path / "bkp"
    log_dir.mkdir()
    backup_dir.mkdir()
    monkeypatch.setattr(_settings, 'LOG_DIR', log_dir)
    monkeypatch.setattr(_settings, 'BACKUP_DIR', backup_dir)

    # create valid license file
    lic = license_manager.generate_license("TRIAL")
    license_manager.activate_license(lic)
    # create fake log entries
    (log_dir / "sistema.log").write_text("line1\nline2\nline3\n")
    # create some backups
    for i in range(3):
        (backup_dir / f"{i}.db").write_text("")

    info = system_info.get_system_info()
    assert info["license_valid"] is True
    assert info["backup_count"] == 3
    assert "line3" in info["recent_logs"]
    assert info["local_version"] == update_manager.get_local_version()


if __name__ == "__main__":
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as td:
        p = Path(td)
        test_empty_state(p)
        test_populated_state(p)
    print("system info tests passed")