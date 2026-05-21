from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="easyhire")
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/easyhire")

    # Redis / Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0")

    # API
    PROJECT_NAME: str = "EasyHire Scout"
    API_V1_STR: str = "/api/v1"

    # LLM Configuration (DeepSeek API)
    # Uses LLM_API_KEY from .env for maximum security
    LLM_API_KEY: str = Field(
        description="DeepSeek API key for skill matching (REQUIRED - from .env)"
    )
    DEEPSEEK_BASE_URL: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek API base URL"
    )
    DEEPSEEK_MODEL: str = Field(
        default="deepseek-chat",
        description="Model to use for skill extraction"
    )
    DEEPSEEK_TIMEOUT: int = Field(
        default=30,
        description="API request timeout in seconds"
    )
    DEEPSEEK_MAX_RETRIES: int = Field(
        default=3,
        description="Max retry attempts for transient failures"
    )
    
    # Feature Flags
    ENABLE_LLM_MATCHING: bool = Field(
        default=True,
        description="Enable Tier 3 LLM matching (disable to save API costs)"
    )
    
    # Alias for backward compatibility
    @property
    def DEEPSEEK_API_KEY(self) -> str:
        """Alias to LLM_API_KEY for code consistency."""
        return self.LLM_API_KEY

settings = Settings()
