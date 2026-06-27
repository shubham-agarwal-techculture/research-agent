"""Password hashing and JWT utilities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from research_agent.config import ApiConfig


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str, config: ApiConfig) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=config.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, config.jwt_secret, algorithm="HS256")


def decode_access_token(token: str, config: ApiConfig) -> str | None:
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=["HS256"])
    except JWTError:
        return None
    subject = payload.get("sub")
    return str(subject) if subject is not None else None
