import json
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "DATAEXPIRY API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    DATABASE_URL: str = "sqlite:///./dataexpiry.db"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS origins
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]

    # AI Governance Engine Configuration (Google Gemini)
    AI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    # Gemini Free-Tier Optimization Settings (Quota: ~15 RPM)
    GEMINI_RPM_LIMIT: int = 10  # Conservative process-local limit below ~15 RPM quota
    GEMINI_RATE_LIMIT_RPM: int = 10  # Alias for rate limit RPM
    GEMINI_MAX_RETRIES: int = 2  # Max retries on 429 / 503 errors
    GEMINI_TIMEOUT_SECONDS: float = 8.0  # HTTP request timeout in seconds
    GEMINI_CACHE_TTL_SECONDS: int = 3600  # In-memory cache TTL in seconds (1 hour)
    GEMINI_CACHE_MAX_ENTRIES: int = 1000  # Max cached assessments
    GEMINI_SKIP_IDENTICAL_PURPOSE: bool = False  # Skip LLM call if purpose & usage are identical or placeholder

    # Security Configuration
    ALLOW_DEV_HEADER_AUTH: bool = False  # Explicit opt-in required to allow header-based dev identity in development mode

    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parent.parent.parent / ".env", ".env"),
        extra="ignore",
    )

    def get_cors_origins(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            try:
                return json.loads(self.CORS_ORIGINS)
            except Exception:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

settings = Settings()
