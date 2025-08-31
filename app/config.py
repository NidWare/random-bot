from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False)

    BOT_TOKEN: str = "8448748393:AAGIVP3dnJLIGzvjbBkYDfGdOd1QYqPTlno"
    WEBAPP_URL: str
    DATABASE_URL: str = "sqlite:////app/data/app.db"
    LOG_LEVEL: str = "INFO"


settings = Settings()


class ServiceContext(BaseModel):
    database_url: str
    bot_token: str
    webapp_url: str


def build_service_context() -> ServiceContext:
    return ServiceContext(
        database_url=settings.DATABASE_URL,
        bot_token=settings.BOT_TOKEN,
        webapp_url=settings.WEBAPP_URL,
    ) 