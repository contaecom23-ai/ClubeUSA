"""Password hashing and verification using bcrypt directly.

Uses bcrypt >= 4.x directly (passlib[bcrypt] has a compatibility issue with bcrypt>=4).
Passwords are truncated to 72 bytes before hashing — bcrypt's native limit.
"""
import bcrypt

_ROUNDS = 12  # cost factor; ~250ms per hash on commodity hardware
_MAX_BYTES = 72  # bcrypt hard limit


def hash_password(plain: str) -> str:
    truncated = plain.encode("utf-8")[:_MAX_BYTES]
    return bcrypt.hashpw(truncated, bcrypt.gensalt(rounds=_ROUNDS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        truncated = plain.encode("utf-8")[:_MAX_BYTES]
        return bcrypt.checkpw(truncated, hashed.encode("utf-8"))
    except Exception:
        return False
