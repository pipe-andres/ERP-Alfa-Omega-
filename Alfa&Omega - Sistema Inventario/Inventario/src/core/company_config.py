"""Módulo para configuración específica de la empresa cliente.
Los datos se almacenan en config/company.json
"""
import json
from pathlib import Path

COMPANY_FILE = Path(__file__).parent.parent.parent / "config" / "company.json"

DEFAULTS = {
    "name": "Mi Empresa",
    "logo": None,
    "address": "Dirección",
    "phone": "",
    "currency": "USD",
    "tax_rate": 0.0,
}


def load_company() -> dict:
    if COMPANY_FILE.exists():
        try:
            return json.loads(COMPANY_FILE.read_text())
        except Exception:
            pass
    # return defaults and ensure file
    save_company(DEFAULTS)
    return DEFAULTS.copy()


def save_company(data: dict) -> None:
    COMPANY_FILE.parent.mkdir(exist_ok=True)
    merged = DEFAULTS.copy()
    merged.update(data)
    COMPANY_FILE.write_text(json.dumps(merged))


# convenience setters/getters

def get_company_name() -> str:
    return load_company().get("name")

def set_company_name(name: str) -> None:
    cfg = load_company()
    cfg["name"] = name
    save_company(cfg)
