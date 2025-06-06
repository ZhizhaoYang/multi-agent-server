from typing import Optional, TypeAlias, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, SecretStr
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from dotenv import load_dotenv, find_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import logging
import json
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.language_models.llms import LLM

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())

# BasedLLMType: TypeAlias = BaseChatModel | LLM

# Load API Keys from environment variables
DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY") # Added for OpenAI
HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
# Add other API keys here as you support more providers, e.g., ANTHROPIC_API_KEY

if not DEEPSEEK_API_KEY:
    logger.warning("DEEPSEEK_API_KEY not found. DeepSeek LLM creation will fail if attempted.")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found. OpenAI LLM creation will fail if attempted.")

class LLMInitializationError(Exception):
    """Custom exception raised when LLM initialization fails."""
    pass

class LLMProviders(Enum):
    """Enum for supported LLM providers."""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    # Add other providers like LLAMA, ANTHROPIC etc. here

class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    provider: str = Field(..., description="The provider name (e.g., 'deepseek', 'openai').")
    model: str = Field(..., description="The specific model name for the provider (e.g., 'deepseek-chat', 'gpt-4o').")
    temperature: float = Field(0.1, ge=0.0, le=2.0, description="Sampling temperature (0.0 to 2.0).")
    extra_params: Optional[Dict[str, Any]] = None

class LLMFactory:
    """Factory for creating LLM instances based on configuration.
    Supports multiple providers like DeepSeek and OpenAI.
    Caches initialized LLM instances for reuse.
    """
    _llm_cache: dict[str, BaseChatModel] = {}

    @classmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def create_llm(cls, config: LLMConfig) -> BaseChatModel:
        """Creates an LLM instance from the given configuration.
        Uses a cache to return existing instances for the same configuration.

        Args:
            config: LLMConfig specifying the provider, model, and other parameters.
        Returns:
            An instance of a class derived from BaseChatModel (e.g., ChatDeepSeek, ChatOpenAI).
        Raises:
            LLMInitializationError: If API key is not set for the provider or initialization fails.
            ValueError: If the provider in config is not recognized (should be caught by Pydantic/Enum).
        """
        config_dict = config.model_dump(exclude_none=True)
        cache_key = json.dumps(config_dict, sort_keys=True)

        if cache_key in cls._llm_cache:
            logger.info(f"Returning cached LLM instance for config: {cache_key}")
            return cls._llm_cache[cache_key]

        logger.debug(f"Attempting to create LLM with config: {json.dumps(config_dict)}") # Use dumped dict for logging consistency

        llm_instance: BaseChatModel
        input_params = {
            "model": config.model,
            "temperature": config.temperature,
        }
        if config.extra_params is not None:
            input_params.update(config.extra_params)

        logger.info(f"LLM config: {config}")

        try:
            if config.provider == LLMProviders.DEEPSEEK.value:
                if not DEEPSEEK_API_KEY:
                    logger.error("DEEPSEEK_API_KEY is not set. Cannot initialize DeepSeek LLM.")
                    raise LLMInitializationError("DEEPSEEK_API_KEY is not configured.")
                llm_instance = ChatDeepSeek(
                    api_key=SecretStr(DEEPSEEK_API_KEY),
                    **input_params
                )
                logger.info(f"Successfully created ChatDeepSeek instance for model: {config.model}")

            elif config.provider == LLMProviders.OPENAI.value:
                if not OPENAI_API_KEY:
                    logger.error("OPENAI_API_KEY is not set. Cannot initialize OpenAI LLM.")
                    raise LLMInitializationError("OPENAI_API_KEY is not configured.")
                llm_instance = ChatOpenAI(
                    api_key=SecretStr(OPENAI_API_KEY),
                    **input_params
                )
                logger.info(f"Successfully created ChatOpenAI instance for model: {config.model}")


            # elif config.provider == LLMProviders.HUGGINGFACE.value:
            #     llm_instance = HuggingFaceEndpoint(
            #         huggingfacehub_api_token=HUGGINGFACE_API_KEY,
            #         **input_params
            #     )


            else:
                logger.error(f"Unsupported or unrecognized LLM provider: {config.provider}")
                raise LLMInitializationError(f"Unsupported LLM provider: {config.provider}")

            # Cache the newly created instance
            cls._llm_cache[cache_key] = llm_instance
            logger.info(f"Cached new LLM instance for config: {cache_key}")
            return llm_instance

        except LLMInitializationError: # Re-raise if it's already our custom error
            raise
        except Exception as e:
            logger.error(f"Failed to initialize LLM for provider '{config.provider}', model '{config.model}': {e}", exc_info=True)
            raise LLMInitializationError(f"Error initializing LLM for '{config.provider}' model '{config.model}': {str(e)}") from e

def get_llm(config: LLMConfig) -> BaseChatModel:
    return LLMFactory.create_llm(config)