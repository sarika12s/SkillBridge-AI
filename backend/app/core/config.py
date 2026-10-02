"""Application configuration module using Pydantic Settings."""

from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    PROJECT_NAME: str = "SkillBridge AI"
    OFFICIAL_PROJECT_TITLE: str = (
        "Semantic Resume - Job Matching and Skill Gap Analysis with Personalized Learning Path Recommendation"
    )
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # PostgreSQL / pgvector Database Connection
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "skillbridge_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/skillbridge_db"

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_url(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    # Security & JWT
    JWT_SECRET_KEY: str = "skillbridge_ai_dev_secret_key_change_in_production_32bytes_min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Uploads
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    UPLOAD_DIR: str = "./uploads"

    # AI / Model Paths
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
