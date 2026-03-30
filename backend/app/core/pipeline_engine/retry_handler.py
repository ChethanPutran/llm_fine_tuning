import asyncio
import inspect
import logging
from typing import Dict, Any, Callable, Optional, Tuple, TypeVar, List
from .base import BaseRetryStrategy, RetryStrategy

logger = logging.getLogger(__name__)

T = TypeVar('T')

class FixedRetryStrategy(BaseRetryStrategy):
    """Fixed delay between retries"""
    
    def calculate_delay(self, attempt: int, config: Dict[str, Any]) -> float:
        delay = config.get("delay", 5.0)
        return delay

class ExponentialRetryStrategy(BaseRetryStrategy):
    """Exponential backoff with optional jitter"""
    
    def calculate_delay(self, attempt: int, config: Dict[str, Any]) -> float:
        base_delay = config.get("base_delay", 1.0)
        max_delay = config.get("max_delay", 60.0)
        multiplier = config.get("multiplier", 2.0)
        jitter = config.get("jitter", True)
        
        delay = min(base_delay * (multiplier ** attempt), max_delay)
        
        if jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay

class LinearRetryStrategy(BaseRetryStrategy):
    """Linear increase in delay"""
    
    def calculate_delay(self, attempt: int, config: Dict[str, Any]) -> float:
        base_delay = config.get("base_delay", 1.0)
        increment = config.get("increment", 1.0)
        max_delay = config.get("max_delay", 30.0)
        
        delay = base_delay + (increment * attempt)
        return min(delay, max_delay)
    

class RetryHandler:
    """Handles retry logic with configurable strategies (Strategy pattern)"""
    
    def __init__(self):
        self._strategies = {
            RetryStrategy.FIXED: FixedRetryStrategy(),
            RetryStrategy.EXPONENTIAL: ExponentialRetryStrategy(),
            RetryStrategy.LINEAR: LinearRetryStrategy()
        }
    
    async def execute_with_retry(
        self,
        func: Callable[..., T],
        args: Tuple,
        kwargs: Optional[Dict[str, Any]] = None,
        retry_config: Optional[Dict[str, Any]] = None
    ) -> T:
        """Execute function with retry logic"""
        
        kwargs = kwargs or {}
        retry_config = retry_config or {}
        
        max_retries = retry_config.get("max_retries", 3)
        strategy_name = retry_config.get("strategy", RetryStrategy.EXPONENTIAL)
        retryable_exceptions = retry_config.get("retryable_exceptions", [Exception])
        
        strategy: BaseRetryStrategy = self._strategies.get(strategy_name, self._strategies[RetryStrategy.EXPONENTIAL])
        
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt} for {func.__name__}")
                
                result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Success on retry attempt {attempt} for {func.__name__}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if exception is retryable
                if not self._is_retryable_exception(e, retryable_exceptions):
                    logger.error(f"Non-retryable exception: {e}")
                    raise
                
                if attempt >= max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                    break
                
                # Calculate delay
                delay = strategy.calculate_delay(attempt, retry_config)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s")
                
                await asyncio.sleep(delay)
        
        if last_exception:
            raise last_exception
        
    
    def _is_retryable_exception(self, exception: Exception, retryable_exceptions: List[type]) -> bool:
        """Check if exception is retryable"""
        for exc_type in retryable_exceptions:
            if isinstance(exception, exc_type):
                return True
        return False
