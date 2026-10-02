"""Health check endpoint for platform monitoring."""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="System Health Check")
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    dialect_name = "unknown"
    try:
        bind = db.get_bind()
        dialect_name = bind.dialect.name
    except Exception:
        pass

    engine_display = (
        "PostgreSQL"
        if dialect_name == "postgresql"
        else ("SQLite" if dialect_name == "sqlite" else dialect_name.capitalize())
    )
    db_status = "available"
    pgvector_status = "unavailable"

    # 1. Primary database connectivity check
    try:
        result = db.execute(text("SELECT 1")).scalar()
        if result != 1:
            db_status = "unexpected_response"
    except Exception as e:
        db_status = f"unavailable: {str(e)[:100]}"
        return {
            "status": "degraded",
            "project": settings.PROJECT_NAME,
            "official_title": settings.OFFICIAL_PROJECT_TITLE,
            "environment": settings.ENVIRONMENT,
            "api_version": "v1",
            "database": {
                "status": db_status,
                "engine": engine_display,
                "pgvector": "unavailable",
            },
        }

    # 2. Check pgvector extension ONLY when using PostgreSQL
    if dialect_name == "postgresql":
        try:
            ext_check = db.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            ).scalar()
            pgvector_status = "available" if ext_check == "vector" else "not_installed"
        except Exception:
            pgvector_status = "unavailable"
    else:
        pgvector_status = "unavailable"

    overall_status = "healthy" if db_status == "available" else "degraded"

    return {
        "status": overall_status,
        "project": settings.PROJECT_NAME,
        "official_title": settings.OFFICIAL_PROJECT_TITLE,
        "environment": settings.ENVIRONMENT,
        "api_version": "v1",
        "database": {
            "status": db_status,
            "engine": engine_display,
            "pgvector": pgvector_status,
        },
    }
