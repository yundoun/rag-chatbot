"""Document Retriever for vector similarity search"""

from typing import Any, Dict, List, Optional

from src.config import get_settings
from src.core.models import Document, DocumentMetadata
from src.core.exceptions import NoResultsException
from src.vectorstore import VectorStoreManager


class DocumentRetriever:
    """Document retriever using vector similarity search"""

    def __init__(
        self,
        vector_store: Optional[VectorStoreManager] = None,
        max_results: Optional[int] = None,
    ):
        self.vector_store = vector_store or VectorStoreManager()
        settings = get_settings()
        self.max_results = max_results or settings.max_retrieval_results

    async def retrieve(
        self,
        query: str,
        n_results: Optional[int] = None,
        domains: Optional[List[str]] = None,
    ) -> List[Document]:
        """Retrieve relevant documents for a query"""
        n_results = n_results or self.max_results

        # Build filter if domains specified
        where_filter = None
        if domains:
            where_filter = {"domain": {"$in": domains}}

        # Search vector store
        results = await self.vector_store.search(
            query=query,
            n_results=n_results,
            where=where_filter,
        )

        if not results:
            raise NoResultsException(query)

        # Convert to Document models
        documents = []
        for result in results:
            # Calculate similarity score from distance (cosine)
            # Distance 0 = identical, distance 2 = opposite
            distance = result.get("distance", 0.0)
            similarity = 1 - (distance / 2)

            metadata = result.get("metadata", {})
            doc = Document(
                content=result.get("content", ""),
                metadata=DocumentMetadata(
                    source=metadata.get("source", "unknown"),
                    title=metadata.get("title"),
                    section=metadata.get("section"),
                    chunk_index=metadata.get("chunk_index"),
                    total_chunks=metadata.get("total_chunks"),
                ),
                embedding_score=similarity,
            )
            documents.append(doc)

        return documents

    async def retrieve_by_ids(self, ids: List[str]) -> List[Document]:
        """Retrieve specific documents by their IDs"""
        # This would need to be implemented in VectorStoreManager
        # For now, return empty list as placeholder
        return []

    def calculate_relevance_metrics(
        self, documents: List[Document], threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Calculate relevance metrics for retrieved documents"""
        if not documents:
            return {
                "avg_relevance": 0.0,
                "high_relevance_count": 0,
                "relevance_scores": [],
            }

        scores = [doc.embedding_score or 0.0 for doc in documents]
        high_relevance_count = sum(1 for score in scores if score >= threshold)

        return {
            "avg_relevance": sum(scores) / len(scores) if scores else 0.0,
            "high_relevance_count": high_relevance_count,
            "relevance_scores": scores,
        }
