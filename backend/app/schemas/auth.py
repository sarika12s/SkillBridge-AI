"""Pydantic v2 schemas for authentication and user accounts."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Student or candidate email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    full_name: str = Field(..., min_length=2, max_length=150, description="Candidate's full name")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    current_title: Optional[str] = None
    target_role: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    profile: Optional[UserProfileResponse] = None
