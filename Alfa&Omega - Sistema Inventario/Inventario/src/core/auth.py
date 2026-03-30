# core/auth.py
from __future__ import annotations
from typing import Optional, List, Dict
import tkinter as tk
from tkinter import ttk, messagebox
import re
import secrets

from src.database.connection import get_connection
from src.services.audit import log_event

# =========================================================
# Utilidades de password (hash + verificación)
# =========================================================
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def _hash_password(password: str) -> str:
    """Hash password using sha256_crypt via passlib."""
    return pwd_context.hash(password)

def _verify_password(stored: str, password: str) -> bool:
    """Verify password against sha256_crypt hash."""
    try:
        return pwd_context.verify(password, stored)
    except Exception:
        return False

# =========================================================
# RBAC helpers
# =========================================================
DEFAULT_ROLES = ["ADMIN", "USER", "AUDITOR"]
DEFAULT_PERMS = [
    ("ADMIN",        "Permisos administrativos completos"),
    ("VIEW_AUDIT",   "Ver bitácora de auditoría"),
]

def _is_new_hash(value: str) -> bool:
    """
    True si tiene el formato 'algo:sha256:<salt>:<hexhash>'.
    """
    if not value or not isinstance(value, str):
        return False
    return bool(re.match(r"^algo:sha256:[0-9a-fA-F]{32}:[0-9a-fA-F]{64}$", value))

def ensure_defaults() -> None:
    """
    - Crea roles/permisos base.
    - Crea usuario admin si no existe.
    - Si ya existe 'admin' pero su pass_hash es nulo/viejo, lo REPARA a 'admin123'.
    - Asegura rol ADMIN y permisos.
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            # Roles
            for r in DEFAULT_ROLES:
                cur.execute("INSERT INTO roles(name) VALUES(?) ON CONFLICT(name) DO NOTHING", (r,))

            # Permisos
            for code, desc in DEFAULT_PERMS:
                cur.execute("INSERT INTO permissions(code, description) VALUES(?,?) ON CONFLICT(code) DO NOTHING", (code, desc))

            # ADMIN -> todos los permisos
            cur.execute("SELECT id, code FROM permissions")
            perms = cur.fetchall()
            cur.execute("SELECT id FROM roles WHERE name='ADMIN'")
            admin_role_id = cur.fetchone()[0]
            for pid, _ in perms:
                cur.execute("""
                    INSERT INTO role_permissions(role_id, perm_id) VALUES (?,?) ON CONFLICT(role_id, perm_id) DO NOTHING
                """, (admin_role_id, pid))

            # Usuario admin
            cur.execute("SELECT id, pass_hash, active FROM users WHERE username='admin'")
            row = cur.fetchone()
            if not row:
                # no existe -> crear nuevo con admin123
                ph = _hash_password("admin123")
                cur.execute("""
                    INSERT INTO users (username, name, pass_hash, active)
                    VALUES (?,?,?,1) RETURNING id
                """, ("admin", "Administrador", ph))
                admin_id = int(cur.fetchone()[0])
            else:
                admin_id, pass_hash, active = row[0], row[1], row[2]
                # Si pass_hash es NULL, vacío o no tiene el formato nuevo, lo reparamos
                if not _is_new_hash(pass_hash or ""):
                    ph = _hash_password("admin123")
                    # Usar True en lugar de 1 para compatibilidad con Postgres BOOLEAN
                    cur.execute("UPDATE users SET pass_hash=?, active=? WHERE id=?", (ph, True, admin_id))
                else:
                    # nos aseguramos que esté activo
                    if not active:
                        cur.execute("UPDATE users SET active=? WHERE id=?", (True, admin_id))

            # Asignar rol ADMIN al admin
            cur.execute("""
                INSERT INTO user_roles(user_id, role_id) VALUES (?,?) ON CONFLICT(user_id, role_id) DO NOTHING
            """, (admin_id, admin_role_id))

            conn.commit()
    except Exception as e:
        from src.core.error_handler import log_error
        log_error(e, context={"operation": "ensure_defaults"}, level="CRITICAL")
        raise

def _fetch_user_with_roles(username: str) -> Optional[Dict]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, name, pass_hash, active FROM users WHERE username=?", (username,))
        u = cur.fetchone()
        if not u: return None
        if int(u[4]) != 1: return None
        user_id = u[0]
        cur.execute("""
            SELECT r.name
            FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id=?
        """, (user_id,))
        roles = [r[0] for r in cur.fetchall()]
        return {"id": u[0], "username": u[1], "name": u[2], "pass_hash": u[3], "roles": roles}

def has_perm(user: Dict, perm_or_role: str) -> bool:
    """
    Valida si un usuario tiene permiso (role o permiso granular).
    Si tiene rol ADMIN, siempre True.
    Si 'perm_or_role' está en roles del usuario, True.
    Si 'perm_or_role' es permiso granular (ej: product.delete), valida contra tabla permissions.
    """
    if not user or not perm_or_role:
        return False
    
    target = (perm_or_role or "").upper().strip()
    user_id = user.get("id")
    roles = [r.upper() for r in (user.get("roles") or [])]
    
    # ADMIN siempre tiene acceso total
    if "ADMIN" in roles:
        return True
    
    # Validar si es un rol simple
    if target in roles:
        return True
    
    # Validar si es permiso granular (contiene . como product.delete)
    if "." in target and user_id:
        from src.database import repository
        return repository.user_has_permission(int(user_id), target.lower())
    
    return False

# =========================================================
# API de administración usada por la GUI (Usuarios y Roles)
# =========================================================
def list_roles() -> List[str]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM roles ORDER BY name ASC")
        return [r[0] for r in cur.fetchall()]

def list_users() -> List[Dict]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, name, active FROM users ORDER BY username ASC")
        users = []
        for uid, username, name, active in cur.fetchall():
            cur.execute("""
                SELECT r.name
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id=?
            """, (uid,))
            roles = [r[0] for r in cur.fetchall()]
            users.append({
                "id": uid, "username": username, "name": name,
                "active": bool(active), "roles": roles
            })
        return users

def create_user(username: str, name: str, password: Optional[str] = None, roles: Optional[List[str]] = None) -> tuple[int, Optional[str]]:
    """
    Crea un usuario. Si `password` es None, genera una contraseña temporal y la retorna
    (junto con el `user_id`) para que la GUI pueda mostrársela al administrador.

    Retorna: (user_id, temporary_password_or_None)
    """
    if not username or not name:
        raise ValueError("username y nombre son obligatorios.")
    username = username.strip()
    name = name.strip()
    if len(username) < 3:
        raise ValueError("El username debe tener al menos 3 caracteres.")
    if len(username) > 50:
        raise ValueError("El username no puede superar 50 caracteres.")
    if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
        raise ValueError("El username solo puede contener letras, números, guiones, puntos y guiones bajos.")

    # Si no se pasa contraseña, generamos una temporal
    temp_pass = None
    if not password:
        temp_pass = secrets.token_urlsafe(8)
        password_to_store = temp_pass
    else:
        password_to_store = password

    ph = _hash_password(password_to_store)

    # Roles por defecto si no se indican
    roles = roles if roles is not None else ["USER"]

    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO users (username, name, pass_hash, active)
                VALUES (?,?,?,1)
            """, (username.strip(), name.strip(), ph))
        except Exception as e:
            # Manejar constraint UNIQUE sobre username de forma amigable
            try:
                import sqlite3
                if isinstance(e, sqlite3.IntegrityError):
                    raise ValueError("El nombre de usuario ya existe.") from e
            except Exception:
                # sqlite3 puede no estar disponible en algunos entornos, seguir
                pass
            msg = str(e).lower()
            if "unique" in msg and "user" in msg or "username" in msg:
                raise ValueError("El nombre de usuario ya existe.") from e
            raise

        cur.execute("SELECT last_insert_rowid() as id")
        user_id = int(cur.fetchone()[0])
        _apply_roles(cur, user_id, roles)
        conn.commit()
        return user_id, temp_pass

def set_user_active(user_id: int, active: bool) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET active=? WHERE id=?", (1 if active else 0, int(user_id)))
        if cur.rowcount == 0:
            raise ValueError("Usuario no encontrado.")
        conn.commit()

def reset_password(user_id: int, new_password: Optional[str] = None) -> str:
    """
    Resetea la contraseña de un usuario.
    Si new_password es None, genera una contraseña temporal.
    Retorna la contraseña (temporal o proporcionada).
    """
    # Si no se pasa contraseña, generamos una temporal
    if not new_password:
        new_password = secrets.token_urlsafe(8)
    
    ph = _hash_password(new_password)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET pass_hash=? WHERE id=?", (ph, int(user_id)))
        if cur.rowcount == 0:
            raise ValueError("Usuario no encontrado.")
        conn.commit()
    log_event(user_id, "PASSWORD_RESET", {"user_id": user_id})
    return new_password

def change_password(user_id: int, old_password: str, new_password: str) -> None:
    if not new_password:
        raise ValueError("Nueva contraseña requerida.")
    if len(new_password) < 6:
        raise ValueError("La nueva contraseña debe tener al menos 6 caracteres.")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT pass_hash FROM users WHERE id=?", (int(user_id),))
        row = cur.fetchone()
        if not row: raise ValueError("Usuario no encontrado.")
        if not _verify_password(row[0], old_password):
            raise ValueError("La contraseña actual no es correcta.")
        ph = _hash_password(new_password)
        cur.execute("UPDATE users SET pass_hash=? WHERE id=?", (ph, int(user_id)))
        conn.commit()

def set_user_roles(user_id: int, roles: List[str]) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        _apply_roles(cur, int(user_id), roles)
        conn.commit()

def _apply_roles(cur, user_id: int, roles: List[str]) -> None:
    roles = roles or []
    roles = [r.strip().upper() for r in roles if r and r.strip()]
    # limpiar
    cur.execute("DELETE FROM user_roles WHERE user_id=?", (user_id,))
    # insertar
    for r in roles:
        cur.execute("SELECT id FROM roles WHERE name=?", (r,))
        rr = cur.fetchone()
        if not rr:
            # crear role si no existe (flexible)
            cur.execute("INSERT INTO roles(name) VALUES(?) ON CONFLICT(name) DO NOTHING", (r,))
            cur.execute("SELECT id FROM roles WHERE name=?", (r,))
            result = cur.fetchone()
            role_id = int(result[0]) if result else None
        else:
            role_id = rr[0]
        if role_id is None:
            continue  # FIX: no insertar user_role con role_id NULL
        cur.execute("INSERT INTO user_roles(user_id, role_id) VALUES(?,?) ON CONFLICT(user_id, role_id) DO NOTHING", (user_id, role_id))

# =========================================================
# Diálogos GUI (Login & Cambiar contraseña)
# =========================================================
class LoginDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Iniciar sesión")
        self.resizable(False, False)
        self.result = None

        frm = ttk.Frame(self, padding=12); frm.grid(sticky="nsew")
        ttk.Label(frm, text="Usuario").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ttk.Label(frm, text="Contraseña").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.e_user = ttk.Entry(frm, width=24)
        self.e_pass = ttk.Entry(frm, width=24, show="*")
        self.e_user.grid(row=0, column=1, padx=6, pady=6)
        self.e_pass.grid(row=1, column=1, padx=6, pady=6)

        btns = ttk.Frame(frm); btns.grid(row=2, column=0, columnspan=2, sticky="e")
        ttk.Button(btns, text="Cancelar", command=self._cancel).pack(side="right", padx=(6,0))
        ttk.Button(btns, text="Entrar", command=self._ok).pack(side="right")

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())
        self.transient(master); self.grab_set(); self.e_user.focus()
        self.wait_window(self)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _ok(self):
        username = (self.e_user.get() or "").strip()
        password = (self.e_pass.get() or "").strip()
        if not username or not password:
            messagebox.showerror("Login", "Ingresa usuario y contraseña.")
            return

        try:
            u = _fetch_user_with_roles(username)
            if not u:
                messagebox.showerror("Login", "Usuario no existe o está inactivo.")
                return
            if not _verify_password(u["pass_hash"], password):
                messagebox.showerror("Login", "Contraseña incorrecta.")
                return

            # empaquetar lo que espera la GUI
            self.result = {"id": u["id"], "username": u["username"], "name": u["name"], "roles": u["roles"]}
            self.destroy()
        except Exception as e:
            import traceback
            messagebox.showerror("Error en Login", f"Error: {str(e)}\n\n{traceback.format_exc()}")
            return

class ChangePasswordDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Cambiar contraseña")
        self.resizable(False, False)
        self.result = None

        frm = ttk.Frame(self, padding=12); frm.grid(sticky="nsew")
        ttk.Label(frm, text="Actual").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ttk.Label(frm, text="Nueva").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        ttk.Label(frm, text="Confirmar").grid(row=2, column=0, sticky="e", padx=6, pady=6)

        self.e_old = ttk.Entry(frm, width=24, show="*"); self.e_old.grid(row=0, column=1, padx=6, pady=6)
        self.e_new1 = ttk.Entry(frm, width=24, show="*"); self.e_new1.grid(row=1, column=1, padx=6, pady=6)
        self.e_new2 = ttk.Entry(frm, width=24, show="*"); self.e_new2.grid(row=2, column=1, padx=6, pady=6)

        btns = ttk.Frame(frm); btns.grid(row=3, column=0, columnspan=2, sticky="e")
        ttk.Button(btns, text="Cancelar", command=self._cancel).pack(side="right", padx=(6,0))
        ttk.Button(btns, text="Guardar", command=self._ok).pack(side="right")

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())
        self.transient(master); self.grab_set(); self.e_old.focus()
        self.wait_window(self)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _ok(self):
        old = self.e_old.get() or ""
        n1 = self.e_new1.get() or ""
        n2 = self.e_new2.get() or ""
        if not old or not n1 or not n2:
            messagebox.showerror("Cambiar contraseña", "Completa todos los campos.")
            return
        if n1 != n2:
            messagebox.showerror("Cambiar contraseña", "La nueva contraseña y la confirmación no coinciden.")
            return
        if len(n1) < 6:
            messagebox.showerror("Cambiar contraseña", "La nueva contraseña debe tener al menos 6 caracteres.")
            return
        self.result = (old, n1, n2)
        self.destroy()