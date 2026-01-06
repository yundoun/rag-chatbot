"""Performance metrics collection and reporting"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class MetricPoint:
    """Single metric data point"""

    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric"""

    count: int
    total: float
    min: float
    max: float
    avg: float
    p50: float  # median
    p95: float
    p99: float

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "total": round(self.total, 2),
            "min": round(self.min, 2),
            "max": round(self.max, 2),
            "avg": round(self.avg, 2),
            "p50": round(self.p50, 2),
            "p95": round(self.p95, 2),
            "p99": round(self.p99, 2),
        }


class MetricsCollector:
    """Collects and aggregates performance metrics"""

    def __init__(self, retention_minutes: int = 60):
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._lock = Lock()
        self._retention_minutes = retention_minutes

    def record(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a metric value"""
        with self._lock:
            point = MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                tags=tags or {},
            )
            self._metrics[name].append(point)
            self._cleanup_old_metrics(name)

    def increment(self, name: str, amount: int = 1) -> None:
        """Increment a counter"""
        with self._lock:
            self._counters[name] += amount

    def decrement(self, name: str, amount: int = 1) -> None:
        """Decrement a counter"""
        with self._lock:
            self._counters[name] -= amount

    def get_counter(self, name: str) -> int:
        """Get counter value"""
        with self._lock:
            return self._counters.get(name, 0)

    def _cleanup_old_metrics(self, name: str) -> None:
        """Remove metrics older than retention period"""
        cutoff = datetime.utcnow() - timedelta(minutes=self._retention_minutes)
        self._metrics[name] = [p for p in self._metrics[name] if p.timestamp > cutoff]

    def get_summary(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        minutes: Optional[int] = None,
    ) -> Optional[MetricSummary]:
        """Get summary statistics for a metric"""
        with self._lock:
            points = self._metrics.get(name, [])

            if not points:
                return None

            # Filter by time window
            if minutes:
                cutoff = datetime.utcnow() - timedelta(minutes=minutes)
                points = [p for p in points if p.timestamp > cutoff]

            # Filter by tags
            if tags:
                points = [
                    p
                    for p in points
                    if all(p.tags.get(k) == v for k, v in tags.items())
                ]

            if not points:
                return None

            values = sorted([p.value for p in points])
            count = len(values)
            total = sum(values)

            return MetricSummary(
                count=count,
                total=total,
                min=values[0],
                max=values[-1],
                avg=total / count,
                p50=values[int(count * 0.5)],
                p95=values[min(int(count * 0.95), count - 1)],
                p99=values[min(int(count * 0.99), count - 1)],
            )

    def get_all_summaries(
        self, minutes: Optional[int] = None
    ) -> Dict[str, MetricSummary]:
        """Get summaries for all metrics"""
        summaries = {}
        with self._lock:
            for name in self._metrics.keys():
                summary = self.get_summary(name, minutes=minutes)
                if summary:
                    summaries[name] = summary
        return summaries

    def get_all_counters(self) -> Dict[str, int]:
        """Get all counter values"""
        with self._lock:
            return dict(self._counters)

    def reset(self) -> None:
        """Reset all metrics and counters"""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()


# Metric names constants
class MetricNames:
    """Standard metric names"""

    # Response time metrics
    RESPONSE_TIME = "response_time_ms"
    LLM_LATENCY = "llm_latency_ms"
    RETRIEVAL_LATENCY = "retrieval_latency_ms"
    EMBEDDING_LATENCY = "embedding_latency_ms"

    # LLM metrics
    PROMPT_TOKENS = "prompt_tokens"
    COMPLETION_TOKENS = "completion_tokens"
    TOTAL_TOKENS = "total_tokens"
    LLM_CALLS = "llm_calls"

    # Retrieval metrics
    DOCUMENTS_RETRIEVED = "documents_retrieved"
    RETRIEVAL_SCORE = "retrieval_score"

    # Cache metrics
    CACHE_HITS = "cache_hits"
    CACHE_MISSES = "cache_misses"
    CACHE_SIZE = "cache_size"

    # Error metrics
    ERRORS = "errors"
    RETRIES = "retries"

    # Request metrics
    REQUESTS_TOTAL = "requests_total"
    REQUESTS_ACTIVE = "requests_active"

    # HITL metrics
    CLARIFICATIONS_TRIGGERED = "clarifications_triggered"
    CLARIFICATIONS_RESOLVED = "clarifications_resolved"

    # Web search metrics
    WEB_SEARCHES = "web_searches"
    WEB_SEARCH_FALLBACKS = "web_search_fallbacks"


class Timer:
    """Context manager for timing code blocks"""

    def __init__(
        self,
        collector: MetricsCollector,
        metric_name: str,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.collector = collector
        self.metric_name = metric_name
        self.tags = tags
        self.start_time: Optional[float] = None
        self.elapsed_ms: Optional[float] = None

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time is not None:
            self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
            self.collector.record(self.metric_name, self.elapsed_ms, self.tags)

    async def __aenter__(self) -> "Timer":
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)


def timed_metric(
    collector: MetricsCollector,
    metric_name: str,
    tags: Optional[Dict[str, str]] = None,
):
    """Decorator to record function execution time as a metric"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        import asyncio
        from functools import wraps

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            with Timer(collector, metric_name, tags):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            with Timer(collector, metric_name, tags):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def set_metrics_collector(collector: MetricsCollector) -> None:
    """Set global metrics collector instance"""
    global _global_collector
    _global_collector = collector


@dataclass
class RequestMetrics:
    """Metrics for a single request"""

    trace_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    response_time_ms: Optional[float] = None

    # LLM metrics
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    llm_latency_ms: float = 0.0

    # Retrieval metrics
    documents_retrieved: int = 0
    retrieval_latency_ms: float = 0.0

    # Flow metrics
    clarification_count: int = 0
    retry_count: int = 0
    used_web_search: bool = False
    used_cache: bool = False

    def finish(self) -> None:
        """Mark request as finished"""
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.response_time_ms = (
                self.end_time - self.start_time
            ).total_seconds() * 1000

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace_id,
            "response_time_ms": (
                round(self.response_time_ms, 2) if self.response_time_ms else None
            ),
            "llm": {
                "calls": self.llm_calls,
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.prompt_tokens + self.completion_tokens,
                "latency_ms": round(self.llm_latency_ms, 2),
            },
            "retrieval": {
                "documents": self.documents_retrieved,
                "latency_ms": round(self.retrieval_latency_ms, 2),
            },
            "flow": {
                "clarifications": self.clarification_count,
                "retries": self.retry_count,
                "used_web_search": self.used_web_search,
                "used_cache": self.used_cache,
            },
        }

    def record_to_collector(self, collector: MetricsCollector) -> None:
        """Record all metrics to collector"""
        tags = {"trace_id": self.trace_id}

        if self.response_time_ms:
            collector.record(MetricNames.RESPONSE_TIME, self.response_time_ms, tags)

        collector.record(MetricNames.LLM_CALLS, self.llm_calls, tags)
        collector.record(MetricNames.PROMPT_TOKENS, self.prompt_tokens, tags)
        collector.record(MetricNames.COMPLETION_TOKENS, self.completion_tokens, tags)
        collector.record(
            MetricNames.TOTAL_TOKENS,
            self.prompt_tokens + self.completion_tokens,
            tags,
        )
        collector.record(MetricNames.LLM_LATENCY, self.llm_latency_ms, tags)
        collector.record(
            MetricNames.DOCUMENTS_RETRIEVED, self.documents_retrieved, tags
        )
        collector.record(MetricNames.RETRIEVAL_LATENCY, self.retrieval_latency_ms, tags)

        collector.increment(MetricNames.REQUESTS_TOTAL)

        if self.clarification_count > 0:
            collector.increment(
                MetricNames.CLARIFICATIONS_TRIGGERED, self.clarification_count
            )

        if self.used_web_search:
            collector.increment(MetricNames.WEB_SEARCH_FALLBACKS)

        if self.used_cache:
            collector.increment(MetricNames.CACHE_HITS)
