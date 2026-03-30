"""ACL helper layer for RBAC checks.

This module provides a small API to check permissions and bootstrap common
permissions/roles. It delegates to `src.database.repository` for DB operations.
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime

from src.database import repository


def has_permission(user_id: int, perm_code: str) -> bool:
    """Return True if the user has the given permission code via any role."""
    return repository.user_has_permission(int(user_id), perm_code)


def ensure_core_permissions() -> None:
    """Ensure the minimal set of permissions and roles exist.

    Creates permissions and a default 'admin' role that receives all perms.
    Safe to call multiple times.
    """
    perms = [
        ("product.create", "Create products"),
        ("product.update", "Update products"),
        ("product.delete", "Delete products"),
        ("product.view", "View products"),
        ("warehouse.transfer", "Transfer between warehouses"),
        ("kardex.view", "View kardex")
    ]
    # create permissions
    perm_ids = []
    for code, desc in perms:
        pid = repository.create_permission(code, desc)
        perm_ids.append(pid)

    # create admin role and assign all perms
    admin_role = repository.create_role("admin")
    for pid in perm_ids:
        repository.add_permission_to_role(admin_role, pid)


def assign_role_to_user(user_id: int, role_name: str) -> None:
    """Assign a role (by name) to a user (creates role if missing)."""
    role_id = repository.create_role(role_name)
    repository.add_role_to_user(user_id, role_id)
