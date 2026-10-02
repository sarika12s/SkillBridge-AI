"""API dependencies for request handling, database sessions, and authentication."""

from typing import Generator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency to extract user ID from JWT bearer token."""
    if not token:
        raise UnauthorizedException("Authentication token required.")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedException("Invalid or expired authentication token.")
    return str(payload["sub"])
