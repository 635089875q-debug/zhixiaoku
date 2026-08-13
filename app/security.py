from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings


password_hash = PasswordHash.recommended()


def hash_password(password):
    return password_hash.hash(password)


def verify_password(
    password,
    hashed_password
):
    return password_hash.verify(
        password,
        hashed_password
    )


def create_access_token(user_id):
    if not settings.JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY未配置"
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token):
    if not settings.JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY未配置"
        )

    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    user_id = payload.get("sub")

    if user_id is None:
        raise jwt.InvalidTokenError(
            "令牌中缺少用户信息"
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError) as error:
        raise jwt.InvalidTokenError(
            "令牌中的用户信息无效"
        ) from error

    if user_id <= 0:
        raise jwt.InvalidTokenError(
            "令牌中的用户信息无效"
        )

    return user_id
