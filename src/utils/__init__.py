"""Utility modules for RAG Chatbot"""

from src.utils.error_handler import (
    ErrorHandler,
    ErrorResponse,
    RetryConfig,
    get_error_handler,
    handle_api_error,
    with_retry,
)
from src.utils.logger import (
    JSONFormatter,
    LogContext,
    StructuredLogger,
    get_logger,
    get_trace_id,
    set_trace_id,
    setup_logging,
    timed,
    with_trace_id,
)
from src.utils.metrics import (
    CacheStats,
    MetricNames,
    MetricsCollector,
    MetricSummary,
    RequestMetrics,
    Timer,
    get_metrics_collector,
    timed_metric,
)
from src.utils.cache import (
    CacheEntry,
    QueryCache,
    TTLCache,
    cached,
    get_embedding_cache,
    get_query_cache,
)

__all__ = [
    # Error handling
    "ErrorHandler",
    "ErrorResponse",
    "RetryConfig",
    "get_error_handler",
    "handle_api_error",
    "with_retry",
    # Logging
    "JSONFormatter",
    "LogContext",
    "StructuredLogger",
    "get_logger",
    "get_trace_id",
    "set_trace_id",
    "setup_logging",
    "timed",
    "with_trace_id",
    # Metrics
    "CacheStats",
    "MetricNames",
    "MetricsCollector",
    "MetricSummary",
    "RequestMetrics",
    "Timer",
    "get_metrics_collector",
    "timed_metric",
    # Cache
    "CacheEntry",
    "QueryCache",
    "TTLCache",
    "cached",
    "get_embedding_cache",
    "get_query_cache",
]
