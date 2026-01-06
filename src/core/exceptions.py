"""Custom exceptions for RAG Chatbot"""

from enum import Enum
from typing import Optional


class ErrorType(str, Enum):
    """Types of errors in the RAG system"""
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    PARSING = "parsing"
    NO_RESULT = "no_result"
    VECTOR_STORE = "vector_store"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    LLM = "llm"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    UNKNOWN = "unknown"


class FallbackAction(str, Enum):
    """Fallback actions when errors occur"""
    RETRY = "retry"
    WEB_SEARCH = "web_search"
    ASK_USER = "ask_user"
    FAIL = "fail"
    USE_CACHE = "use_cache"


class RAGException(Exception):
    """Base exception for RAG system"""

    error_type: ErrorType = ErrorType.UNKNOWN
    fallback_action: FallbackAction = FallbackAction.FAIL
    user_message_ko: str = "오류가 발생했습니다. 잠시 후 다시 시도해 주세요."

    def __init__(
        self,
        message: str,
        recoverable: bool = True,
        error_type: Optional[ErrorType] = None,
        user_message: Optional[str] = None,
    ):
        self.message = message
        self.recoverable = recoverable
        if error_type:
            self.error_type = error_type
        if user_message:
            self.user_message_ko = user_message
        super().__init__(message)


class LLMException(RAGException):
    """LLM related exception"""

    error_type = ErrorType.LLM
    fallback_action = FallbackAction.RETRY
    user_message_ko = "AI 서비스에 문제가 발생했습니다. 잠시 후 다시 시도해 주세요."


class APIRateLimitException(LLMException):
    """API rate limit exceeded"""

    error_type = ErrorType.RATE_LIMIT
    fallback_action = FallbackAction.RETRY
    user_message_ko = "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요."

    def __init__(self, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after}s",
            recoverable=True,
        )
        self.retry_after = retry_after


class APITimeoutException(LLMException):
    """API timeout exception"""

    error_type = ErrorType.TIMEOUT
    fallback_action = FallbackAction.RETRY
    user_message_ko = "응답 시간이 초과되었습니다. 다시 시도해 주세요."

    def __init__(self, timeout: int = 30):
        super().__init__(
            f"API request timed out after {timeout}s",
            recoverable=True,
        )
        self.timeout = timeout


class ParsingException(RAGException):
    """LLM output parsing failure"""

    error_type = ErrorType.PARSING
    fallback_action = FallbackAction.RETRY
    user_message_ko = "응답 처리 중 문제가 발생했습니다. 다시 시도해 주세요."

    def __init__(self, message: str = "Failed to parse LLM response"):
        super().__init__(message, recoverable=True)


class RetrievalException(RAGException):
    """Retrieval related exception"""

    error_type = ErrorType.VECTOR_STORE
    fallback_action = FallbackAction.WEB_SEARCH
    user_message_ko = "문서 검색 중 문제가 발생했습니다."


class NoResultsException(RetrievalException):
    """No search results found"""

    error_type = ErrorType.NO_RESULT
    fallback_action = FallbackAction.WEB_SEARCH
    user_message_ko = "관련 문서를 찾을 수 없습니다. 다른 키워드로 검색해 보세요."

    def __init__(self, query: str = ""):
        message = "No relevant documents found"
        if query:
            message = f"No relevant documents found for query: {query}"
        super().__init__(message, recoverable=True)
        self.query = query


class VectorStoreException(RAGException):
    """Vector store exception"""

    error_type = ErrorType.VECTOR_STORE
    fallback_action = FallbackAction.FAIL
    user_message_ko = "데이터베이스 연결에 문제가 발생했습니다."


class ConfigurationException(RAGException):
    """Configuration error"""

    error_type = ErrorType.CONFIGURATION
    fallback_action = FallbackAction.FAIL
    user_message_ko = "시스템 설정에 문제가 있습니다. 관리자에게 문의해 주세요."

    def __init__(self, message: str):
        super().__init__(message, recoverable=False)


class ValidationException(RAGException):
    """Input validation exception"""

    error_type = ErrorType.VALIDATION
    fallback_action = FallbackAction.ASK_USER
    user_message_ko = "입력값이 올바르지 않습니다. 다시 확인해 주세요."

    def __init__(self, message: str):
        super().__init__(message, recoverable=False)


class NetworkException(RAGException):
    """Network related exception"""

    error_type = ErrorType.NETWORK
    fallback_action = FallbackAction.RETRY
    user_message_ko = "네트워크 연결에 문제가 발생했습니다. 인터넷 연결을 확인해 주세요."

    def __init__(self, message: str = "Network error occurred"):
        super().__init__(message, recoverable=True)


class AuthenticationException(RAGException):
    """Authentication error"""

    error_type = ErrorType.AUTHENTICATION
    fallback_action = FallbackAction.FAIL
    user_message_ko = "인증에 실패했습니다. API 키를 확인해 주세요."

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, recoverable=False)
