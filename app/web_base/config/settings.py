from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = "dev"
    LLM_API_KEY: str | None = None
    VERSION: str = "0.1.0"
    # DB_URL: str = "sqlite:///./chatbot.db"

    class Config:
        env_file = ".env"
        extra = "ignore"



