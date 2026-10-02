"""Authentication and user management service."""

import uuid
from typing import Tuple
from sqlalchemy.orm import Session
from app.models.user import User, UserProfile
from app.schemas.auth import UserRegisterRequest
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import ValidationException, UnauthorizedException, NotFoundException


def register_user(req: UserRegisterRequest, db: Session) -> Tuple[User, str]:
    """Register a new user account with hashed password and return (user, access_token)."""
    normalized_email = req.email.strip().lower()

    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise ValidationException("An account with this email address already exists.")

    new_user = User(
        id=uuid.uuid4(),
        email=normalized_email,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name.strip(),
        role="student",
        is_active=True,
    )
    db.add(new_user)

    # Initialize empty profile
    profile = UserProfile(
        id=uuid.uuid4(),
        user_id=new_user.id,
    )
    db.add(profile)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(subject=str(new_user.id), claims={"email": new_user.email})
    return new_user, token


def authenticate_user(email: str, password: str, db: Session) -> Tuple[User, str]:
    """Verify user credentials and return (user, access_token)."""
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Incorrect email or password.")

    if not user.is_active:
        raise UnauthorizedException("User account is inactive.")

    token = create_access_token(subject=str(user.id), claims={"email": user.email})
    return user, token


def get_user_by_id(user_id: str, db: Session) -> User:
    """Retrieve user by UUID string."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise UnauthorizedException("Invalid user ID in authentication token.")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise NotFoundException("User account not found.")
    return user
