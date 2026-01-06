"""Centralized error handling with retry logic and user-friendly messages"""

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

from src.core.exceptions import (
    RAGException,
    ErrorType,
    FallbackAction,
    APIRateLimitException,
    APITimeoutException,
    NetworkException,
    ParsingException,
    LLMException,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class ErrorResponse:
    """Standardized error response schema"""

    error_type: ErrorType
    user_message: str
    recoverable: bool
    fallback_action: FallbackAction
    details: Optional[str] = None
    retry_after: Optional[int] = None
    trace_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        result = {
            "error_type": self.error_type.value,
            "user_message": self.user_message,
            "recoverable": self.recoverable,
            "fallback_action": self.fallback_action.value,
        }
        if self.details:
            result["details"] = self.details
        if self.retry_after:
            result["retry_after"] = self.retry_after
        if self.trace_id:
            result["trace_id"] = self.trace_id
        return result


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = field(
        default_factory=lambda: (
            APIRateLimitException,
            APITimeoutException,
            NetworkException,
            ParsingException,
        )
    )


class ErrorHandler:
    """Centralized error handler for RAG system"""

    # Default Korean error messages by error type
    DEFAULT_MESSAGES = {
        ErrorType.RATE_LIMIT: "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
        ErrorType.TIMEOUT: "응답 시간이 초과되었습니다. 다시 시도해 주세요.",
        ErrorType.PARSING: "응답 처리 중 문제가 발생했습니다. 다시 시도해 주세요.",
        ErrorType.NO_RESULT: "관련 문서를 찾을 수 없습니다. 다른 키워드로 검색해 보세요.",
        ErrorType.VECTOR_STORE: "데이터베이스 연결에 문제가 발생했습니다.",
        ErrorType.CONFIGURATION: "시스템 설정에 문제가 있습니다. 관리자에게 문의해 주세요.",
        ErrorType.VALIDATION: "입력값이 올바르지 않습니다. 다시 확인해 주세요.",
        ErrorType.LLM: "AI 서비스에 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.",
        ErrorType.NETWORK: "네트워크 연결에 문제가 발생했습니다. 인터넷 연결을 확인해 주세요.",
        ErrorType.AUTHENTICATION: "인증에 실패했습니다. API 키를 확인해 주세요.",
        ErrorType.UNKNOWN: "오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    }

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_config = retry_config or RetryConfig()
        self._error_counts: dict[str, int] = {}

    def handle_error(
        self,
        error: Exception,
        trace_id: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> ErrorResponse:
        """
        Handle an exception and return a standardized ErrorResponse.

        Args:
            error: The exception to handle
            trace_id: Optional trace ID for logging
            context: Optional context information

        Returns:
            ErrorResponse with user-friendly message and recovery info
        """
        # Log the error
        self._log_error(error, trace_id, context)

        # Determine error type and response
        if isinstance(error, RAGException):
            return self._handle_rag_exception(error, trace_id)
        else:
            return self._handle_generic_exception(error, trace_id)

    def _handle_rag_exception(
        self, error: RAGException, trace_id: Optional[str]
    ) -> ErrorResponse:
        """Handle RAGException subclasses"""
        retry_after = None
        if isinstance(error, APIRateLimitException):
            retry_after = error.retry_after

        return ErrorResponse(
            error_type=error.error_type,
            user_message=error.user_message_ko,
            recoverable=error.recoverable,
            fallback_action=error.fallback_action,
            details=str(error) if logger.isEnabledFor(logging.DEBUG) else None,
            retry_after=retry_after,
            trace_id=trace_id,
        )

    def _handle_generic_exception(
        self, error: Exception, trace_id: Optional[str]
    ) -> ErrorResponse:
        """Handle non-RAG exceptions"""
        # Map common exceptions to error types
        error_type = self._classify_exception(error)
        user_message = self.DEFAULT_MESSAGES.get(
            error_type, self.DEFAULT_MESSAGES[ErrorType.UNKNOWN]
        )

        return ErrorResponse(
            error_type=error_type,
            user_message=user_message,
            recoverable=error_type
            in {ErrorType.TIMEOUT, ErrorType.NETWORK, ErrorType.RATE_LIMIT},
            fallback_action=self._get_fallback_action(error_type),
            details=str(error) if logger.isEnabledFor(logging.DEBUG) else None,
            trace_id=trace_id,
        )

    def _classify_exception(self, error: Exception) -> ErrorType:
        """Classify a generic exception into an ErrorType"""
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()

        if "timeout" in error_str or "timeout" in error_type_name:
            return ErrorType.TIMEOUT
        elif "rate" in error_str and "limit" in error_str:
            return ErrorType.RATE_LIMIT
        elif "connection" in error_str or "network" in error_str:
            return ErrorType.NETWORK
        elif "auth" in error_str or "401" in error_str or "403" in error_str:
            return ErrorType.AUTHENTICATION
        elif "parse" in error_str or "json" in error_str:
            return ErrorType.PARSING
        elif "validation" in error_str or "invalid" in error_str:
            return ErrorType.VALIDATION
        else:
            return ErrorType.UNKNOWN

    def _get_fallback_action(self, error_type: ErrorType) -> FallbackAction:
        """Get appropriate fallback action for error type"""
        fallback_map = {
            ErrorType.RATE_LIMIT: FallbackAction.RETRY,
            ErrorType.TIMEOUT: FallbackAction.RETRY,
            ErrorType.PARSING: FallbackAction.RETRY,
            ErrorType.NO_RESULT: FallbackAction.WEB_SEARCH,
            ErrorType.VECTOR_STORE: FallbackAction.WEB_SEARCH,
            ErrorType.LLM: FallbackAction.RETRY,
            ErrorType.NETWORK: FallbackAction.RETRY,
            ErrorType.VALIDATION: FallbackAction.ASK_USER,
            ErrorType.CONFIGURATION: FallbackAction.FAIL,
            ErrorType.AUTHENTICATION: FallbackAction.FAIL,
            ErrorType.UNKNOWN: FallbackAction.FAIL,
        }
        return fallback_map.get(error_type, FallbackAction.FAIL)

    def _log_error(
        self,
        error: Exception,
        trace_id: Optional[str],
        context: Optional[dict],
    ) -> None:
        """Log error with context"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "trace_id": trace_id,
            "context": context,
        }

        if isinstance(error, RAGException):
            error_info["rag_error_type"] = error.error_type.value
            error_info["recoverable"] = error.recoverable

        if logger.isEnabledFor(logging.DEBUG):
            error_info["traceback"] = traceback.format_exc()

        logger.error(f"Error occurred: {error_info}")

    def calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        import random

        delay = self.retry_config.base_delay * (
            self.retry_config.exponential_base**attempt
        )
        delay = min(delay, self.retry_config.max_delay)

        if self.retry_config.jitter:
            # Add random jitter (±25%)
            jitter = delay * 0.25 * (2 * random.random() - 1)
            delay += jitter

        return delay

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an error should be retried.

        Args:
            error: The exception that occurred
            attempt: Current attempt number

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.retry_config.max_retries:
            return False

        if isinstance(error, self.retry_config.retryable_exceptions):
            return True

        if isinstance(error, RAGException):
            return error.recoverable and error.fallback_action == FallbackAction.RETRY

        return False


def with_retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        config: Retry configuration
        on_retry: Optional callback called on each retry

    Returns:
        Decorated function
    """
    _config = config or RetryConfig()
    handler = ErrorHandler(retry_config=_config)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_error: Optional[Exception] = None

            for attempt in range(_config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    if not handler.should_retry(e, attempt):
                        raise

                    delay = handler.calculate_retry_delay(attempt)

                    if on_retry:
                        on_retry(e, attempt)

                    logger.warning(
                        f"Retry {attempt + 1}/{_config.max_retries} "
                        f"for {func.__name__} after {delay:.2f}s: {e}"
                    )

                    await asyncio.sleep(delay)

            # Should not reach here, but raise last error if we do
            if last_error:
                raise last_error
            raise RuntimeError("Unexpected retry loop exit")

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_error: Optional[Exception] = None

            for attempt in range(_config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    if not handler.should_retry(e, attempt):
                        raise

                    delay = handler.calculate_retry_delay(attempt)

                    if on_retry:
                        on_retry(e, attempt)

                    logger.warning(
                        f"Retry {attempt + 1}/{_config.max_retries} "
                        f"for {func.__name__} after {delay:.2f}s: {e}"
                    )

                    time.sleep(delay)

            if last_error:
                raise last_error
            raise RuntimeError("Unexpected retry loop exit")

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def handle_api_error(
    error: Exception,
    trace_id: Optional[str] = None,
) -> dict:
    """
    Convenience function to handle errors and return API-ready response.

    Args:
        error: The exception to handle
        trace_id: Optional trace ID

    Returns:
        Dictionary suitable for API error response
    """
    handler = ErrorHandler()
    response = handler.handle_error(error, trace_id)
    return response.to_dict()


# Global error handler instance
_global_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _global_handler
    if _global_handler is None:
        _global_handler = ErrorHandler()
    return _global_handler


def set_error_handler(handler: ErrorHandler) -> None:
    """Set global error handler instance"""
    global _global_handler
    _global_handler = handler
