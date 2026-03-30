"""Tests for the licensing subsystem."""
import sys
import os
import json
from pathlib import Path
# ensure project root in path (three levels up)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core import license_manager

# use the same path used by license_manager
TEMP_LICENSE = license_manager.LICENSE_FILE

def teardown_module(module):
    # clean up license file after tests
    try:
        if TEMP_LICENSE.exists():
            TEMP_LICENSE.unlink()
    except Exception:
        pass


def test_generate_and_validate_trial():
    # ensure no license on disk
    try:
        if license_manager.LICENSE_FILE.exists():
            license_manager.LICENSE_FILE.unlink()
    except Exception:
        pass
    lic_str = license_manager.generate_license("TRIAL")
    assert "TRIAL" in lic_str
    # not yet saved, so validate_license should be False
    assert not license_manager.validate_license()

    activated = license_manager.activate_license(lic_str)
    assert activated
    assert license_manager.validate_license()


def test_tampered_license_fails():
    lic_str = license_manager.generate_license("PRO")
    lic = json.loads(lic_str)
    # tamper with plan
    lic["plan"] = "ENTERPRISE"
    tampered = json.dumps(lic)
    assert not license_manager.activate_license(tampered)


def test_expired_license():
    # create license with expiration in the past
    import datetime
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    data = {
        "machine": license_manager._machine_hash(),
        "plan": "TRIAL",
        "expiration": past.isoformat(),
    }
    payload = json.dumps(data, sort_keys=True)
    data["signature"] = license_manager._sign(payload)
    lic_str = json.dumps(data)
    # write directly to file
    TEMP_LICENSE.write_text(lic_str)
    assert not license_manager.validate_license()


if __name__ == "__main__":
    test_generate_and_validate_trial()
    test_tampered_license_fails()
    test_expired_license()
    print("license tests passed")
