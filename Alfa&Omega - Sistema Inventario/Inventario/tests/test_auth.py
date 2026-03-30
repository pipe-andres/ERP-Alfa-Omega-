import pytest
from src.core.auth import _hash_password, _verify_password, ensure_defaults

def test_hash_verify():
    pw = 'secret123'
    h = _hash_password(pw)
    assert _verify_password(h, pw)

def test_ensure_defaults_runs():
    # should not throw
    ensure_defaults()
    assert True
