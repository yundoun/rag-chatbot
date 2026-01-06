"""LLM Provider module"""

from typing import Optional

from .provider import LLMProvider
from .openai_provider import OpenAIProvider

_llm_provider: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Get singleton LLM provider instance"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = OpenAIProvider()
    return _llm_provider


__all__ = ["LLMProvider", "OpenAIProvider", "get_llm_provider"]
