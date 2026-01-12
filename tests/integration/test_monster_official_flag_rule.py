from types import SimpleNamespace
from backend.authorization.dependencies import enforce_monster_official_flag_on_save


def test_admin_forces_official_true():
    actor = SimpleNamespace(role=SimpleNamespace(value="ADMIN"))
    monster = SimpleNamespace(is_official=False)

    enforce_monster_official_flag_on_save(actor, monster)

    assert monster.is_official is True


def test_dm_forces_official_false():
    actor = SimpleNamespace(role=SimpleNamespace(value="DM"))
    monster = SimpleNamespace(is_official=True)

    enforce_monster_official_flag_on_save(actor, monster)

    assert monster.is_official is False