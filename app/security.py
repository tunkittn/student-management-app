"""Password hashing helpers based on salted PBKDF2-HMAC-SHA256."""

import hashlib
import hmac
import secrets


ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
SALT_BYTES = 16


def hash_password(password: str, iterations: int = ITERATIONS) -> str:
    if not password:
        raise ValueError("Password must not be empty")
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        iterations,
    ).hex()
    return f"{ALGORITHM}${iterations}${salt}${digest}"


def is_password_hash(value: str | None) -> bool:
    return bool(value and value.startswith(f"{ALGORITHM}$"))


def verify_password(password: str, encoded: str) -> bool:
    if not password or not is_password_hash(encoded):
        return False
    try:
        algorithm, iteration_text, salt, expected = encoded.split("$", 3)
        if algorithm != ALGORITHM:
            return False
        iterations = int(iteration_text)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("ascii"),
            iterations,
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False
