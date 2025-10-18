# -*- coding: utf-8 -*-
"""Application settings using pydantic."""
from __future__ import annotations

from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    mongo_uri: str = Field("mongodb://127.0.0.1:27017", env="MONGO_URI")
    mongo_db_name: str = Field("talkingcat", env="MONGO_DB_NAME")
    jwt_secret_key: str = Field("super-secret-key", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(14, env="REFRESH_TOKEN_EXPIRE_DAYS")

    class Config:
        env_file = ".env"
        case_sensitive = False

default_settings = Settings()


@lru_cache
def get_settings() -> Settings:
    return default_settings
