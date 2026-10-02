"""Custom exceptions and error response utilities."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class SkillBridgeException(HTTPException):
    """Base exception for all domain-specific errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An unexpected error occurred in SkillBridge AI.",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(SkillBridgeException):
    def __init__(self, detail: str = "Resource not found."):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ValidationException(SkillBridgeException):
    def __init__(self, detail: str = "Input validation failed."):
        # Support both HTTP_422_UNPROCESSABLE_CONTENT and legacy name
        status_code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
        super().__init__(
            status_code=status_code, detail=detail
        )


class UnauthorizedException(SkillBridgeException):
    def __init__(self, detail: str = "Could not validate credentials."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(SkillBridgeException):
    def __init__(self, detail: str = "Operation not permitted."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
