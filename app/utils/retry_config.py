"""
Clean retry configuration using tenacity for multi-agent workflow.
Balanced approach: simple to use, easy to extend, production-ready.
"""

import logging
import asyncio
from typing import Callable, Any, Type, Union, Tuple
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random,
    retry_if_exception_type,
    before_sleep_log,
    AsyncRetrying,
    RetryError
)

logger = logging.getLogger(__name__)

# Exception types that are worth retrying (transient failures)
RETRYABLE_EXCEPTIONS = (
    # Network/connection issues
    ConnectionError,
    TimeoutError,
    asyncio.TimeoutError,
    # HTTP client exceptions (add specific ones as needed)
    # requests.RequestException,  # Uncomment if using requests
    # httpx.RequestError,         # Uncomment if using httpx
)

# Exception types that should NOT be retried (permanent failures)
NON_RETRYABLE_EXCEPTIONS = (
    # Authentication/authorization errors
    PermissionError,
    # Input validation errors
    ValueError,
    TypeError,
    KeyError,
    # File system errors
    FileNotFoundError,
)

# Retry configurations for different scenarios
RETRY_CONFIGS = {
    # For department nodes - moderate retry strategy
    "department": {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=1, min=2, max=8) + wait_random(0, 1),
        "retry": retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        "before_sleep": before_sleep_log(logger, logging.WARNING),
        "reraise": True,
    },

    # For HQ/supervisor nodes - quick failure strategy
    "supervisor": {
        "stop": stop_after_attempt(2),
        "wait": wait_exponential(multiplier=1, min=1, max=4) + wait_random(0, 0.5),
        "retry": retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        "before_sleep": before_sleep_log(logger, logging.WARNING),
        "reraise": True,
    },

    # For LLM calls - aggressive retry for rate limits
    "llm": {
        "stop": stop_after_attempt(4),
        "wait": wait_exponential(multiplier=2, min=1, max=30) + wait_random(0, 2),
        "retry": retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        "before_sleep": before_sleep_log(logger, logging.INFO),
        "reraise": True,
    },

    # For external API calls - balanced approach
    "external_api": {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=1.5, min=1, max=10) + wait_random(0, 1),
        "retry": retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        "before_sleep": before_sleep_log(logger, logging.WARNING),
        "reraise": True,
    }
}

def with_retry(config_name: str = "department"):
    """
    Decorator to add retry behavior to functions.

    Args:
        config_name: Which retry configuration to use

    Usage:
        @with_retry("department")
        async def my_department_function():
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        config = RETRY_CONFIGS.get(config_name, RETRY_CONFIGS["department"])
        return retry(**config)(func)

    return decorator

async def retry_async_call(
    operation: Callable,
    *args,
    config_name: str = "department",
    **kwargs
) -> Any:
    """
    Retry an async operation without using decorators.
    Useful for dynamic retry scenarios.

    Args:
        operation: The async function to retry
        *args: Arguments for the operation
        config_name: Which retry configuration to use
        **kwargs: Keyword arguments for the operation

    Usage:
        result = await retry_async_call(
            my_risky_function,
            arg1, arg2,
            config_name="llm",
            kwarg1=value1
        )
    """
    config = RETRY_CONFIGS.get(config_name, RETRY_CONFIGS["department"])

    try:
        async for attempt in AsyncRetrying(**config):
            with attempt:
                return await operation(*args, **kwargs)
    except RetryError as e:
        logger.error(f"Operation {operation.__name__} failed after all retries: {e}")
        raise

def get_retry_stats(func: Callable) -> dict:
    """Get retry statistics from a decorated function."""
    if hasattr(func, 'retry') and hasattr(func.retry, 'statistics'):
        return func.retry.statistics
    return {}

# Specific decorators for common use cases
def retry_department(func: Callable) -> Callable:
    """Shortcut decorator for department operations."""
    return with_retry("department")(func)

def retry_supervisor(func: Callable) -> Callable:
    """Shortcut decorator for supervisor operations."""
    return with_retry("supervisor")(func)

def retry_llm(func: Callable) -> Callable:
    """Shortcut decorator for LLM operations."""
    return with_retry("llm")(func)

def retry_external_api(func: Callable) -> Callable:
    """Shortcut decorator for external API operations."""
    return with_retry("external_api")(func)

# Advanced: Custom retry for specific error types
def retry_on_errors(
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]],
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10
):
    """
    Create a custom retry decorator for specific exception types.

    Args:
        exceptions: Exception type(s) to retry on
        max_attempts: Maximum number of attempts
        min_wait: Minimum wait time between retries
        max_wait: Maximum wait time between retries
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait) + wait_random(0, 1),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )

# Circuit breaker simulation using failure tracking
class SimpleCircuitBreaker:
    """
    Simple circuit breaker that can be used with retry decorators.
    Tracks failures and temporarily blocks calls after threshold.
    """

    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.is_open = False

    def call(self, func: Callable, *args, **kwargs):
        """Call a function through the circuit breaker."""
        import time

        current_time = time.time()

        # Check if circuit should be closed (reset)
        if self.is_open and (current_time - self.last_failure_time) > self.reset_timeout:
            self.is_open = False
            self.failures = 0
            logger.info("Circuit breaker reset - allowing calls")

        # If circuit is open, reject the call
        if self.is_open:
            logger.warning("Circuit breaker is open - blocking call")
            raise ConnectionError("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            # Success - reset failure count
            self.failures = 0
            return result
        except Exception as e:
            # Failure - increment counter
            self.failures += 1
            self.last_failure_time = current_time

            # Open circuit if threshold reached
            if self.failures >= self.failure_threshold:
                self.is_open = True
                logger.error(f"Circuit breaker opened after {self.failures} failures")

            raise

# Example circuit breaker instance
department_circuit_breaker = SimpleCircuitBreaker(failure_threshold=3, reset_timeout=120)

def with_circuit_breaker(circuit_breaker: SimpleCircuitBreaker):
    """Decorator to add circuit breaker protection to functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await circuit_breaker.call(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return circuit_breaker.call(func, *args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator