from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserRegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_]+$"
    )
    password: str = Field(
        min_length=8,
        max_length=128
    )

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class UserLoginRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50
    )
    password: str = Field(
        min_length=1,
        max_length=128
    )

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CurrentUserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime
    updated_at: datetime
