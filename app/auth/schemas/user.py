from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.auth.models.user import UserStatus
from app.core.db import FilterParam, ListParams, SortParam


class UserBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

    username: str | None = Field(min_length=3, max_length=50)
    email: EmailStr | None
    status_id: UserStatus | None = None


# Requests


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)


class PasswordRestoreRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    token: str
    password: str


class UserSortParam(SortParam):
    field: Literal['id', 'username', 'status_id', 'created_at']


class UserFilterParam(FilterParam):
    field: Literal['id', 'username', 'status_id']


class UserListParams(ListParams):
    sort: list[UserSortParam] | None = Field(None, description='Sorting parameters')  # type: ignore
    filters: list[UserFilterParam] | None = Field(None, description='Filtering parameters')  # type: ignore


# Responses


class UserResponse(UserBase):
    id: int


# Repository DTOs


class UserCreate(UserCreateRequest):
    status_id: UserStatus | None = None
    password: str | None = Field(default=None, min_length=8)  # type: ignore
    password_hash: str | None = None


class UserUpdate(UserUpdateRequest):
    status_id: UserStatus | None = None
    password_hash: str | None = None


# User DTO


class UserDTO(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
