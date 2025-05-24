from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, SecretStr
from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv, find_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import os

load_dotenv(find_dotenv())

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


class LLMInitializationError(Exception):
    """Exception raised when LLM initialization fails."""
    pass


class LLMConfig(BaseModel):
    """Centralized configuration for LLM providers"""
    provider: Literal['deepseek'] = 'deepseek'
    model: str = Field(..., min_length=3)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    # max_tokens: Optional[int] = Field(None, gt=0)
    # api_version: Optional[str] = None
    # request_timeout: int = Field(30, gt=0)
    # max_retries: int = Field(3, ge=0)


class LLMFactory:

    @classmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def create_llm(cls, config: LLMConfig) -> ChatDeepSeek:
        print("**** create_llm ****")
        print(config)

        provider = config.provider
        print("provider ->", provider)
        llm = None

        # print("DEEPSEEK_API_KEY ->", DEEPSEEK_API_KEY)
        # print("provider ->", provider)
        try:
            if provider == 'deepseek':
                model = config.model if config.model else "deepseek-chat"

                llm = ChatDeepSeek(
                    model=model,
                    api_key=SecretStr(DEEPSEEK_API_KEY) if DEEPSEEK_API_KEY else None,
                    **config.model_dump(exclude={"model", "provider"})
                )

            if llm is None:
                print("**** create_llm error ****")
                raise ValueError(f"Unsupported LLM provider: {provider}")

            return llm

        except Exception as e:
            print("**** create_llm error ****")
            print(e)
            raise LLMInitializationError(f"Unexpected error during LLM initialization: {str(e)}") from e

def get_llm(config: LLMConfig) -> ChatDeepSeek:
    return LLMFactory.create_llm(config)