"""Tests for company configuration module."""
import sys
from pathlib import Path
import json

# ensure path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core import company_config


def teardown_module(module):
    # remove config file after tests
    try:
        company_config.COMPANY_FILE.unlink()
    except Exception:
        pass


def test_load_defaults():
    # remove any existing file so defaults are returned
    try:
        company_config.COMPANY_FILE.unlink()
    except Exception:
        pass
    cfg = company_config.load_company()
    assert cfg["name"] == company_config.DEFAULTS["name"]


def test_save_and_load():
    company_config.save_company({"name": "ACME Corp", "currency": "EUR"})
    cfg = company_config.load_company()
    assert cfg["name"] == "ACME Corp"
    assert cfg["currency"] == "EUR"


def test_corrupted_file_resets_to_defaults():
    # write invalid json to file
    company_config.COMPANY_FILE.write_text("{{not json}}")
    cfg = company_config.load_company()
    assert cfg["name"] == company_config.DEFAULTS["name"]

if __name__ == "__main__":
    test_load_defaults()
    test_save_and_load()
    print("company config tests passed")