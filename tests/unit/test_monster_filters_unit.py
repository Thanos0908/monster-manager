from types import SimpleNamespace
from backend.authorization.dependencies import monster_filter_for_user

def test_monster_filter_for_admin_is_noop_true():
    admin = SimpleNamespace(role=SimpleNamespace(value="ADMIN"))
    expr = monster_filter_for_user(admin)
    assert str(expr).lower() in ("true", "true_")  # dialect differences

def test_monster_filter_for_dm_is_official_only():
    dm = SimpleNamespace(role=SimpleNamespace(value="DM"))
    expr = monster_filter_for_user(dm)
    # should reference is_official
    assert "is_official" in str(expr)