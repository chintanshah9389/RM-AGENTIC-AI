from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Agentic AI Banking CRM"
    app_env: str = "development"
    app_debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "sqlite:///./agentic_banking_crm.db"

    jwt_secret: str = "change-this-for-real-environment"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    llm_provider: str = "mock"
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "nvidia/nemotron-3.5-bolt-e4b"

    # langgraph (architecture default) | native
    orchestrator_engine: str = "langgraph"

    messaging_provider: str = "mock"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    data_seed: int = 42
    customer_seed_count: int = 5000
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
