import jwt
from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.database import get_user_by_id
from app.security import decode_access_token


bearer_scheme = HTTPBearer(
    auto_error=False
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials
    | None = Depends(bearer_scheme)
):
    credentials_error = HTTPException(
        status_code=401,
        detail="登录状态无效或已过期",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise credentials_error

    try:
        user_id = decode_access_token(
            credentials.credentials
        )
    except (jwt.InvalidTokenError, ValueError):
        raise credentials_error

    user = get_user_by_id(user_id)

    if not user:
        raise credentials_error

    return user


def require_admin(
    current_user=Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )

    return current_user
