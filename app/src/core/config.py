from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    dev = "dev"
    staging = "staging"
    prod = "prod"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    version: str = "0.0.0"
    environment: Environment = Environment.dev
    build_id: str = "unknown"


settings = Settings()
