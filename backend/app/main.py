"""FastAPI main application entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.exceptions import SkillBridgeException
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.skills import router as skills_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.matching import router as matching_router
from app.api.v1.careers import router as careers_router
from app.api.v1.learning_paths import router as learning_paths_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.progress import router as progress_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    # Startup: ensure upload directory exists
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # Shutdown clean up logic


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        f"**Official Project Title:** {settings.OFFICIAL_PROJECT_TITLE}\n\n"
        "AI-powered student career intelligence platform providing semantic resume-job matching, "
        "explainable ATS readiness analysis, job compatibility evaluation, and prerequisite-aware learning paths."
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(SkillBridgeException)
async def skillbridge_exception_handler(
    request: Request, exc: SkillBridgeException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


# Root Health & Info Redirect
@app.get("/", tags=["Root"])
def root_info():
    return {
        "project": settings.PROJECT_NAME,
        "official_title": settings.OFFICIAL_PROJECT_TITLE,
        "documentation": f"{settings.API_V1_PREFIX}/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "phase": "Phase 7 - Interactive Career Intelligence Dashboard, Version Tracking & Progress Analytics",
    }


# Mount API Routers (support both /api/v1 and /api)
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(resumes_router, prefix=settings.API_V1_PREFIX)
app.include_router(skills_router, prefix=settings.API_V1_PREFIX)
app.include_router(jobs_router, prefix=settings.API_V1_PREFIX)
app.include_router(matching_router, prefix=settings.API_V1_PREFIX)
app.include_router(careers_router, prefix=settings.API_V1_PREFIX)
app.include_router(learning_paths_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(progress_router, prefix=settings.API_V1_PREFIX)

# Also mount under /api for convenience
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(resumes_router, prefix="/api")
app.include_router(skills_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(matching_router, prefix="/api")
app.include_router(careers_router, prefix="/api")
app.include_router(learning_paths_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(progress_router, prefix="/api")
