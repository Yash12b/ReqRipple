from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserRegister(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, max_length=255)
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, max_length=255)
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
