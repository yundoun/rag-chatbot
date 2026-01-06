"""Embedding Provider abstraction"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.llm import OpenAIProvider


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for list of texts"""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI Embedding Provider implementation"""

    # Embedding dimensions for different models
    DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, llm_provider: Optional[OpenAIProvider] = None):
        self.llm_provider = llm_provider or OpenAIProvider()
        self._model = self.llm_provider.embedding_model

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for list of texts"""
        return await self.llm_provider.get_embeddings(texts)

    def get_dimension(self) -> int:
        """Get embedding dimension for current model"""
        return self.DIMENSIONS.get(self._model, 1536)
