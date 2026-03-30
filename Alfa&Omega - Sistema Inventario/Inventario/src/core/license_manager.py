"""Módulo de gestión de licencias.

La licencia se guarda en config/license.key y contiene:
- machine_hash
- plan
- expiration (ISO string)
- signature HMAC

Tipos de plan: TRIAL (30d), PRO, ENTERPRISE

Se valida al iniciar el sistema y bloquea si inválida.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import sys

# clave secreta para firmar licencias. En un producto real estaría
# protegida y no en texto plano.
import base64 as _b64
_SECRET_KEY = _b64.b64decode(
    b"QWxmYU9tZWdhRVJQMjAyNlNlY3JldEtleUxhdGFt"
)

# Para compatibilidad con PyInstaller
if getattr(sys, '_MEIPASS', None):
    # Si está empaquetado, buscar en el directorio del exe
    BASE_DIR = Path(sys._MEIPASS)
else:
    # En desarrollo, usar el directorio del proyecto
    BASE_DIR = Path(__file__).parent.parent.parent

LICENSE_FILE = BASE_DIR / "config" / "license.key"


def _machine_hash() -> str:
    """Identificador estable de la máquina, inmune a cambios de NICs virtuales
    (Docker, VirtualBox, Hyper-V, etc.).

    Windows: usa MachineGuid del registro (asignado en instalación, inmutable)
             combinado con el hostname.
    Otros:   solo hostname (fallback razonable para Linux/macOS).
    """
    import socket
    hostname = socket.gethostname()
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
        )
        machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        raw = f"{machine_guid}-{hostname}".encode("utf-8")
    except Exception:
        # Non-Windows o sin acceso al registro: usar solo hostname
        raw = hostname.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sign(payload: str) -> str:
    return hmac.new(_SECRET_KEY, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_license(plan: str, days: int = None,
                     machine_hash: str = None) -> str:
    """Genera un string de licencia para el plan dado.
    TRIAL asumirá 30 días si no se especifica.
    PRO y ENTERPRISE pueden tener 'days' None (sin expiración) o un valor.
    Si machine_hash se proporciona, se usa ese hash en lugar del de esta máquina.
    """
    plan = plan.upper()
    if plan == "TRIAL":
        exp = datetime.now(timezone.utc) + timedelta(days=days or 30)
    else:
        exp = datetime.now(timezone.utc) + timedelta(days=days) if days else None

    # Usar hash del cliente si se proporciona, sino el de esta máquina
    mhash = machine_hash if machine_hash else _machine_hash()

    data = {
        "machine": mhash,
        "plan": plan,
        "expiration": exp.isoformat() if exp else None,
    }
    payload = json.dumps(data, sort_keys=True)
    signature = _sign(payload)
    data["signature"] = signature
    return json.dumps(data)


def activate_license(lic_str: str) -> bool:
    """Guarda la licencia en disco si válida."""
    try:
        lic = json.loads(lic_str)
    except Exception:
        return False
    # validate signature before saving
    sig = lic.get("signature")
    lic_copy = lic.copy()
    lic_copy.pop("signature", None)
    payload = json.dumps(lic_copy, sort_keys=True)
    if not sig or sig != _sign(payload):
        return False
    # save
    LICENSE_FILE.parent.mkdir(exist_ok=True)
    LICENSE_FILE.write_text(json.dumps(lic))
    return True


def load_license() -> dict | None:
    if not LICENSE_FILE.exists():
        return None
    try:
        data = json.loads(LICENSE_FILE.read_text())
        return data
    except Exception:
        return None


def validate_license() -> bool:
    lic = load_license()
    if not lic:
        return False
    # check machine
    if lic.get("machine") != _machine_hash():
        return False
    # check signature
    sig = lic.get("signature")
    lic_copy = lic.copy()
    lic_copy.pop("signature", None)
    payload = json.dumps(lic_copy, sort_keys=True)
    if sig != _sign(payload):
        return False
    # check expiration
    exp = lic.get("expiration")
    if exp:
        try:
            exp_dt = datetime.fromisoformat(exp)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp_dt:
                return False
        except Exception:
            return False
    return True
