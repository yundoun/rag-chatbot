"""Configuration module for RAG Chatbot"""

from .settings import Settings, get_settings
from .constants import (
    VALID_DOMAINS,
    RELEVANCE_LEVELS,
    MAX_CONTEXT_TOKENS,
    MAX_RESPONSE_TOKENS,
    MAX_DOCUMENT_CHUNK_SIZE,
    DISCLAIMER_MESSAGE,
    WEB_SEARCH_DISCLAIMER,
    ERROR_MESSAGES,
)

__all__ = [
    "Settings",
    "get_settings",
    "VALID_DOMAINS",
    "RELEVANCE_LEVELS",
    "MAX_CONTEXT_TOKENS",
    "MAX_RESPONSE_TOKENS",
    "MAX_DOCUMENT_CHUNK_SIZE",
    "DISCLAIMER_MESSAGE",
    "WEB_SEARCH_DISCLAIMER",
    "ERROR_MESSAGES",
]
