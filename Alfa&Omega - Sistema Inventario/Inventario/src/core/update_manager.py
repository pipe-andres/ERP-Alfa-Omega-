"""Gestión de actualizaciones.
Permite comparar versión local con un archivo remoto o URL.

En un entorno real consultaríamos un servidor, aquí se admite ruta de archivo.
"""
import json
from pathlib import Path
try:
    from packaging import version
except ImportError:
    version = None  # fallback

# requests is optional; network features may not be available in all installs
try:
    import requests
except ImportError:
    requests = None

LOCAL_VERSION_FILE = Path(__file__).parent.parent.parent / "version.json"


def get_local_version() -> str:
    try:
        data = json.loads(LOCAL_VERSION_FILE.read_text())
        return data.get("version", "0.0.0")
    except Exception:
        return "0.0.0"


def get_remote_version(source: str):
    """Obtiene versión remota de archivo local o URL.
    Retorna None si requests no está disponible o hay error de red.
    """
    if source.startswith("http://") or source.startswith("https://"):
        if requests is None:
            return None  # biblioteca no disponible — comportamiento silencioso
        try:
            resp = requests.get(source, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None
    else:
        # treat as file path
        path = Path(source)
        if path.exists():
            return json.loads(path.read_text())
        raise FileNotFoundError(f"Remote version file not found: {source}")


def _parse_ver(v: str):
    if version is not None:
        return version.parse(v)
    # fallback simple tuple of ints
    parts = v.split('.')
    return tuple(int(p) for p in parts if p.isdigit())


def is_update_available(remote_info: dict) -> bool:
    local = get_local_version()
    rem = remote_info.get("version", "0.0.0")
    return _parse_ver(rem) > _parse_ver(local)


def download_update(url: str, dest: Path) -> bool:
    """Descarga archivo de actualización a destino. Retorna True si éxito."""
    if requests is None:
        return False
    try:
        resp = requests.get(url, stream=True, timeout=10)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return True
    except Exception:
        return False


def apply_update(package_path: Path) -> bool:
    """Función stub: en realidad reemplazaría archivos."""
    # Para propósito de fase 4, simplemente retornar True
    return True
