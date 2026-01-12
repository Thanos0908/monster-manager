from types import SimpleNamespace
from backend.authorization.dependencies import _safe_role_str

def test_safe_role_str_lowercases_enum_value():
    user = SimpleNamespace(role=SimpleNamespace(value="ADMIN"))
    assert _safe_role_str(user) == "admin"

def test_safe_role_str_lowercases_string_role():
    user = SimpleNamespace(role="DM")
    assert _safe_role_str(user) == "dm"