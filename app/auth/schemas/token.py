from datetime import datetime

from pydantic import BaseModel, Field


class AccessToken(BaseModel):
    sub: int | None = None
    exp: int | None = None


class PasswordResetToken(BaseModel):
    sub: str
    exp: int


class RefreshTokenBase(BaseModel):
    token: str = Field(min_length=48, max_length=48)
    user_id: int
    expires_at: datetime


class TokenGroup(BaseModel):
    access_token: str
    refresh_token: RefreshTokenBase


# Requests


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Responses


class RefreshTokenResponse(BaseModel):
    token: str = Field(min_length=48, max_length=48)
    expires_at: datetime


class TokenGroupResponse(TokenGroup):
    refresh_token: RefreshTokenResponse  # type: ignore
    token_type: str


# Repository DTOs


class RefreshTokenCreate(RefreshTokenBase):
    token: str = Field(min_length=24, max_length=24)
    hash: str = Field(max_length=255)


class RefreshTokenUpdate(RefreshTokenCreate):
    user_id: int | None = None  # type: ignore
