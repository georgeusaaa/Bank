"""Логика Bank.US без графического интерфейса — её удобно тестировать отдельно."""
import hashlib
import hmac
import json
import os
import secrets
import time

# Новый код можно получить не чаще, чем раз в 180 секунд
GENERATION_COOLDOWN = 180
# После 3 неверных попыток вход для пользователя блокируется на 60 секунд
MAX_ATTEMPTS = 3
LOCKOUT_SECONDS = 60

LETTERS = "ABCD"
DIGITS = "01234567"


def generate_code() -> str:
    """Код формата AA1234. secrets вместо random — его нельзя предсказать."""
    return "".join(secrets.choice(LETTERS) for _ in range(2)) + \
        "".join(secrets.choice(DIGITS) for _ in range(4))


def hash_code(code: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", code.encode(), bytes.fromhex(salt), 100_000).hex()


def make_record(code: str, now: float) -> dict:
    """Запись для JSON: сам код не хранится, только соль и хеш."""
    salt = secrets.token_hex(16)
    return {"salt": salt, "hash": hash_code(code, salt), "created_at": now}


def verify_code(record: dict, code: str) -> bool:
    return hmac.compare_digest(record["hash"], hash_code(code, record["salt"]))


def migrate_users(raw: dict, now: float) -> dict:
    """Старый формат хранил код открытым текстом ("" — кода нет)."""
    users = {}
    for name, value in raw.items():
        if isinstance(value, dict) or value is None:
            users[name] = value
        elif value == "":
            users[name] = None
        else:
            users[name] = make_record(value, now)
    return users


def load_users(path: str, defaults: list, now: float) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return migrate_users(json.load(f), now)
        except (OSError, json.JSONDecodeError):
            pass
    return {name: None for name in defaults}


def save_users(path: str, users: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)


class Bank:
    def __init__(self, users: dict, clock=time.time):
        self.users = users
        self.clock = clock
        self.failed_attempts = {}
        self.locked_until = {}

    def seconds_until_generation(self, name: str) -> int:
        record = self.users.get(name)
        if not record:
            return 0
        left = record["created_at"] + GENERATION_COOLDOWN - self.clock()
        return max(0, int(left + 0.999))

    def generate(self, name: str) -> str:
        """Выдаёт новый код. Бросает ValueError, если кулдаун ещё не прошёл."""
        wait = self.seconds_until_generation(name)
        if wait:
            raise ValueError(f"Новый код можно получить через {wait} сек.")
        code = generate_code()
        self.users[name] = make_record(code, self.clock())
        self.failed_attempts[name] = 0
        return code

    def seconds_locked(self, name: str) -> int:
        left = self.locked_until.get(name, 0) - self.clock()
        return max(0, int(left + 0.999))

    def login(self, name: str, code: str) -> str:
        """Возвращает 'ok', 'wrong', 'locked' или 'no_code'."""
        if self.seconds_locked(name):
            return "locked"
        record = self.users.get(name)
        if not record:
            return "no_code"
        if verify_code(record, code):
            self.failed_attempts[name] = 0
            return "ok"
        self.failed_attempts[name] = self.failed_attempts.get(name, 0) + 1
        if self.failed_attempts[name] >= MAX_ATTEMPTS:
            self.failed_attempts[name] = 0
            self.locked_until[name] = self.clock() + LOCKOUT_SECONDS
            return "locked"
        return "wrong"

    def attempts_left(self, name: str) -> int:
        return MAX_ATTEMPTS - self.failed_attempts.get(name, 0)
