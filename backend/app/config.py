from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env file."""

    # Application
    APP_NAME: str = "ProofLens AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"])

    # Storage
    STORAGE_ROOT: str = "storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = 20
    MAX_DOCUMENTS_PER_WORKSPACE: int = 10

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/prooflens_ai"

    # AI Provider (Gemini)
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_CHAT_MODEL: str = "gemini-2.5-flash"

    # RAG Settings
    RETRIEVAL_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.65
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
