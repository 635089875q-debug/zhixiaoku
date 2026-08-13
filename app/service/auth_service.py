from pymysql.err import IntegrityError

from app.database import (
    create_user,
    get_user_by_username,
)
from app.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotRegisteredError,
)
from app.security import (
    create_access_token,
    hash_password,
    verify_password,
)


def register_user(
    username,
    password
):
    normalized_username = username.strip()

    if get_user_by_username(normalized_username):
        raise UserAlreadyExistsError()

    hashed_password = hash_password(password)

    try:
        user_id = create_user(
            normalized_username,
            hashed_password
        )
    except IntegrityError as error:
        raise UserAlreadyExistsError() from error

    return {
        "id": user_id,
        "username": normalized_username
    }


def login_user(
    username,
    password
):
    normalized_username = username.strip()
    user = get_user_by_username(
        normalized_username
    )

    if not user:
        raise UserNotRegisteredError()

    if not verify_password(
            password,
            user["password_hash"]
    ):
        raise InvalidCredentialsError()

    return {
        "access_token": create_access_token(
            user["id"]
        ),
        "token_type": "bearer"
    }
