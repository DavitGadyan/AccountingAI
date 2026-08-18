"""Password hashing and JWT issuance.

Tokens are HS256, which needs only a shared secret — so PyJWT is used without the
``cryptography`` extra, keeping a Rust build toolchain out of the dependency tree for a
capability (asymmetric signing) this service does not use.

Hashing calls ``bcrypt`` directly rather than through passlib. Passlib has been
unmaintained since 2020 and its backend probing breaks against modern bcrypt releases;
the direct API is three lines and has no such failure mode.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings
from app.core.errors import PermissionDenied

# bcrypt hashes at most 72 bytes and silently ignores the rest. Truncating explicitly
# means a long passphrase is handled predictably instead of raising from inside the
# library on a value the user cannot see.
_MAX_PASSWORD_BYTES = 72


def _encode(raw: str) -> bytes:
    return raw.encode("utf-8")[:_MAX_PASSWORD_BYTES]


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(_encode(raw), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_encode(raw), hashed.encode("utf-8"))
    except ValueError:
        # A malformed stored hash must fail closed, not raise into the login handler
        # where it would leak the difference between "bad password" and "bad record".
        return False


def create_access_token(subject: str, *, firm_id: str, role: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": subject, "firm_id": firm_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:  # pragma: no cover - trivial
        raise PermissionDenied("Invalid or expired credentials") from exc
