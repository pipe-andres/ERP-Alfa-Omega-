import pytest
from src.core import acl
from src.core import auth
from src.database.connection import init_db


def test_rbac_permissions_and_roles():
    init_db()
    # ensure core permissions/roles exist
    acl.ensure_core_permissions()

    # create user
    uid, tmp = auth.create_user("rbac_user", "RBAC User", password="secret", roles=["USER"])
    # by default should not have product.create
    assert not acl.has_permission(uid, "product.create")

    # create role and permission, assign
    repository = __import__("src.database.repository", fromlist=["*"])
    role_id = repository.create_role("testrole")
    perm_id = repository.create_permission("product.create", "Create product test")
    repository.add_permission_to_role(role_id, perm_id)
    repository.add_role_to_user(uid, role_id)

    assert acl.has_permission(uid, "product.create")
