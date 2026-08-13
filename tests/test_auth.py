from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.dependencies import get_current_user
from app.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotRegisteredError,
)
from app.main import app
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.service import auth_service


client = TestClient(app)


def test_password_hash_does_not_store_plain_password():
    plain_password = "secure-password-123"

    hashed_password = hash_password(plain_password)

    assert hashed_password != plain_password
    assert plain_password not in hashed_password
    assert verify_password(
        plain_password,
        hashed_password
    ) is True
    assert verify_password(
        "wrong-password",
        hashed_password
    ) is False


def test_register_service_hashes_password_before_insert(
        monkeypatch
):
    create_calls = []

    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        lambda username: None
    )
    monkeypatch.setattr(
        auth_service,
        "hash_password",
        lambda password: "argon2-hash"
    )
    monkeypatch.setattr(
        auth_service,
        "create_user",
        lambda username, password_hash: (
            create_calls.append(
                (username, password_hash)
            )
            or 15
        )
    )

    result = auth_service.register_user(
        "  bill  ",
        "secure-password-123"
    )

    assert create_calls == [
        ("bill", "argon2-hash")
    ]
    assert result == {
        "id": 15,
        "username": "bill"
    }


def test_register_service_rejects_existing_username(
        monkeypatch
):
    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        lambda username: {
            "id": 1,
            "username": username
        }
    )

    def fail_if_called(*args, **kwargs):
        pytest.fail("重复用户名不应继续创建用户")

    monkeypatch.setattr(
        auth_service,
        "create_user",
        fail_if_called
    )

    with pytest.raises(UserAlreadyExistsError):
        auth_service.register_user(
            "bill",
            "secure-password-123"
        )


def test_register_api_returns_public_user_data(
        monkeypatch
):
    monkeypatch.setattr(
        auth_api,
        "register_user",
        lambda username, password: {
            "id": 20,
            "username": username
        }
    )

    response = client.post(
        "/auth/register",
        json={
            "username": "bill_2026",
            "password": "secure-password-123"
        }
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 20,
        "username": "bill_2026"
    }
    assert "password" not in response.text
    assert "password_hash" not in response.text


def test_register_api_returns_409_for_duplicate_username(
        monkeypatch
):
    def raise_duplicate(username, password):
        raise UserAlreadyExistsError()

    monkeypatch.setattr(
        auth_api,
        "register_user",
        raise_duplicate
    )

    response = client.post(
        "/auth/register",
        json={
            "username": "bill",
            "password": "secure-password-123"
        }
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "用户名已存在"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "ab",
            "password": "secure-password-123"
        },
        {
            "username": "invalid name",
            "password": "secure-password-123"
        },
        {
            "username": "bill",
            "password": "short"
        },
    ]
)
def test_register_api_validates_credentials(payload):
    response = client.post(
        "/auth/register",
        json=payload
    )

    assert response.status_code == 422


def test_access_token_contains_user_id(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(
        settings,
        "JWT_SECRET_KEY",
        "test-secret-key"
    )

    token = create_access_token(12)

    assert decode_access_token(token) == 12


def test_decode_access_token_rejects_expired_token(
        monkeypatch
):
    from app.config import settings

    monkeypatch.setattr(
        settings,
        "JWT_SECRET_KEY",
        "test-secret-key"
    )

    token = jwt.encode(
        {
            "sub": "12",
            "exp": datetime.now(timezone.utc)
            - timedelta(seconds=1)
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_login_service_returns_token(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        lambda username: {
            "id": 8,
            "username": username,
            "password_hash": "stored-hash"
        }
    )
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed_password: (
            password == "correct-password"
            and hashed_password == "stored-hash"
        )
    )
    monkeypatch.setattr(
        auth_service,
        "create_access_token",
        lambda user_id: f"token-for-{user_id}"
    )

    result = auth_service.login_user(
        "  bill  ",
        "correct-password"
    )

    assert result == {
        "access_token": "token-for-8",
        "token_type": "bearer"
    }


def test_login_service_rejects_invalid_password(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        lambda username: {
            "id": 8,
            "username": "bill",
            "password_hash": "stored-hash"
        }
    )
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed_password: False
    )

    with pytest.raises(InvalidCredentialsError):
        auth_service.login_user(
            "bill",
            "wrong-password"
        )


def test_login_service_rejects_unregistered_user(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        lambda username: None
    )

    with pytest.raises(UserNotRegisteredError):
        auth_service.login_user(
            "missing_user",
            "secure-password-123"
        )


def test_login_api_returns_bearer_token(monkeypatch):
    monkeypatch.setattr(
        auth_api,
        "login_user",
        lambda username, password: {
            "access_token": "signed-jwt",
            "token_type": "bearer"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "bill",
            "password": "secure-password-123"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "signed-jwt",
        "token_type": "bearer"
    }


def test_login_api_returns_401_for_invalid_credentials(
        monkeypatch
):
    def raise_invalid_credentials(username, password):
        raise InvalidCredentialsError()

    monkeypatch.setattr(
        auth_api,
        "login_user",
        raise_invalid_credentials
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "bill",
            "password": "wrong-password"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "用户名或密码错误"
    }


def test_login_api_returns_404_for_unregistered_user(
        monkeypatch
):
    def raise_not_registered(username, password):
        raise UserNotRegisteredError()

    monkeypatch.setattr(
        auth_api,
        "login_user",
        raise_not_registered
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "missing_user",
            "password": "secure-password-123"
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "该用户未注册，请先注册"
    }


def test_me_returns_current_user_without_password():
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "username": "bill",
        "role": "admin",
        "created_at": datetime(2026, 8, 12, 10, 0, 0),
        "updated_at": datetime(2026, 8, 12, 10, 0, 0),
    }

    try:
        response = client.get(
            "/auth/me",
            headers={
                "Authorization": "Bearer test-token"
            }
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["username"] == "bill"
    assert response.json()["role"] == "admin"
    assert "password" not in response.text
    assert "password_hash" not in response.text


def test_me_requires_token():
    response = client.get("/auth/me")

    assert response.status_code == 401
