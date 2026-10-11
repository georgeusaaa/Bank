import json

import pytest

from bank_core import GENERATION_COOLDOWN, LOCKOUT_SECONDS, Bank, load_users, migrate_users, save_users


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def bank():
    clock = Clock()
    return Bank({"Анна": None}, clock=clock), clock


def test_generated_code_logs_in(bank):
    b, _ = bank
    code = b.generate("Анна")
    assert len(code) == 6
    assert b.login("Анна", code) == "ok"


def test_code_is_not_stored_in_plain_text(bank):
    b, _ = bank
    code = b.generate("Анна")
    assert code not in json.dumps(b.users)


def test_generation_cooldown(bank):
    b, clock = bank
    b.generate("Анна")
    with pytest.raises(ValueError):
        b.generate("Анна")
    clock.now += GENERATION_COOLDOWN
    b.generate("Анна")


def test_lockout_after_three_wrong_attempts(bank):
    b, clock = bank
    code = b.generate("Анна")
    assert b.login("Анна", "XX0000") == "wrong"
    assert b.login("Анна", "XX0000") == "wrong"
    assert b.login("Анна", "XX0000") == "locked"
    # Даже правильный код не пускает, пока идёт блокировка
    assert b.login("Анна", code) == "locked"
    clock.now += LOCKOUT_SECONDS
    assert b.login("Анна", code) == "ok"


def test_login_without_code(bank):
    b, _ = bank
    assert b.login("Анна", "AA1234") == "no_code"


def test_migrates_old_plain_text_format(tmp_path):
    path = tmp_path / "users.json"
    path.write_text(json.dumps({"Анна": "AB1234", "Олег": ""}), encoding="utf-8")
    users = load_users(str(path), [], now=0)
    b = Bank(users, clock=lambda: 0)
    assert users["Олег"] is None
    assert b.login("Анна", "AB1234") == "ok"
    save_users(str(path), users)
    assert "AB1234" not in path.read_text(encoding="utf-8")
    assert migrate_users(users, 0) == users
