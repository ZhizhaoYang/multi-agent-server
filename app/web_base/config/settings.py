from pydantic_settings import BaseSettings

import os
ENV = os.environ.get("ENV", "dev")

class Settings(BaseSettings):
    ENV: str = ENV
    LLM_API_KEY: str | None = None
    VERSION: str = "0.1.0"

    class Config:
        env_file = ".env"
        extra = "ignore"



