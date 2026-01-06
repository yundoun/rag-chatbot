"""Structured JSON logging with trace ID support"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

# Context variable for trace ID
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

T = TypeVar("T")


def get_trace_id() -> Optional[str]:
    """Get current trace ID from context"""
    return trace_id_var.get()


def set_trace_id(trace_id: Optional[str] = None) -> str:
    """Set trace ID in context, generate new if not provided"""
    if trace_id is None:
        trace_id = str(uuid.uuid4())[:8]
    trace_id_var.set(trace_id)
    return trace_id


def clear_trace_id() -> None:
    """Clear trace ID from context"""
    trace_id_var.set(None)


class JSONFormatter(logging.Formatter):
    """JSON log formatter with structured output"""

    def __init__(self, include_timestamp: bool = True, include_trace_id: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_trace_id = include_trace_id

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if self.include_timestamp:
            log_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        if self.include_trace_id:
            trace_id = get_trace_id()
            if trace_id:
                log_data["trace_id"] = trace_id

        # Add location info
        log_data["location"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "message",
                "thread",
                "threadName",
                "taskName",
            ):
                if not key.startswith("_"):
                    log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False, default=str)


class StructuredLogger:
    """Structured logger with context support"""

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.name = name

    def _log(
        self,
        level: int,
        message: str,
        extra: Optional[dict] = None,
        exc_info: bool = False,
    ) -> None:
        """Internal log method with extra data support"""
        log_extra = extra or {}
        self.logger.log(level, message, extra=log_extra, exc_info=exc_info)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self._log(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self._log(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message"""
        self._log(logging.ERROR, message, kwargs, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log critical message"""
        self._log(logging.CRITICAL, message, kwargs, exc_info=exc_info)

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **kwargs,
    ) -> None:
        """Log HTTP request"""
        self.info(
            f"{method} {path} {status_code}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            **kwargs,
        )

    def log_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
        **kwargs,
    ) -> None:
        """Log LLM API call"""
        self.info(
            f"LLM call to {model}",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration_ms=round(duration_ms, 2),
            **kwargs,
        )

    def log_retrieval(
        self,
        query: str,
        num_results: int,
        duration_ms: float,
        **kwargs,
    ) -> None:
        """Log retrieval operation"""
        self.info(
            f"Retrieved {num_results} documents",
            query_length=len(query),
            num_results=num_results,
            duration_ms=round(duration_ms, 2),
            **kwargs,
        )


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None,
) -> None:
    """
    Setup logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format for logs
        log_file: Optional file path to write logs
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)


def with_trace_id(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to automatically set trace ID for a function"""

    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> T:
        trace_id = kwargs.pop("trace_id", None)
        set_trace_id(trace_id)
        try:
            return await func(*args, **kwargs)
        finally:
            clear_trace_id()

    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> T:
        trace_id = kwargs.pop("trace_id", None)
        set_trace_id(trace_id)
        try:
            return func(*args, **kwargs)
        finally:
            clear_trace_id()

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


class LogContext:
    """Context manager for logging with trace ID"""

    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())[:8]
        self._token = None

    def __enter__(self) -> "LogContext":
        self._token = trace_id_var.set(self.trace_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._token is not None:
            trace_id_var.reset(self._token)

    async def __aenter__(self) -> "LogContext":
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)


def timed(logger: Optional[StructuredLogger] = None):
    """Decorator to log function execution time"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        _logger = logger or get_logger(func.__module__)

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                _logger.debug(
                    f"{func.__name__} completed",
                    function=func.__name__,
                    duration_ms=round(duration_ms, 2),
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _logger.error(
                    f"{func.__name__} failed",
                    function=func.__name__,
                    duration_ms=round(duration_ms, 2),
                    error=str(e),
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                _logger.debug(
                    f"{func.__name__} completed",
                    function=func.__name__,
                    duration_ms=round(duration_ms, 2),
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _logger.error(
                    f"{func.__name__} failed",
                    function=func.__name__,
                    duration_ms=round(duration_ms, 2),
                    error=str(e),
                )
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
