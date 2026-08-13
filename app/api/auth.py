from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotRegisteredError,
)
from app.schemas.auth import (
    CurrentUserResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.service.auth_service import (
    login_user,
    register_user,
)


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", status_code=201)
def register(request: UserRegisterRequest):
    try:
        return register_user(
            request.username,
            request.password
        )

    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="用户名已存在"
        )

    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=500,
            detail="用户注册失败"
        ) from error


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(request: UserLoginRequest):
    try:
        return login_user(
            request.username,
            request.password
        )
    except UserNotRegisteredError:
        raise HTTPException(
            status_code=404,
            detail="该用户未注册，请先注册"
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.get(
    "/me",
    response_model=CurrentUserResponse
)
def get_me(
    current_user=Depends(get_current_user)
):
    return current_user
