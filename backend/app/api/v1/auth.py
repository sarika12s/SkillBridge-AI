"""Authentication API endpoints for registration, login, and profile fetching."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import register_user, authenticate_user, get_user_by_id
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new student/user account."""
    user, token = register_user(req, db)
    return {
        "user": UserResponse.model_validate(user),
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/login", response_model=TokenResponse)
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password to receive a JWT access token."""
    user, token = authenticate_user(req.email, req.password, db)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieve currently authenticated user profile."""
    user = get_user_by_id(user_id, db)
    return UserResponse.model_validate(user)
