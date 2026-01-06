"""ChromaDB Vector Store Manager"""

import os
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import get_settings
from .embeddings import EmbeddingProvider, OpenAIEmbeddingProvider


class VectorStoreManager:
    """ChromaDB Vector Store Manager for document storage and retrieval"""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        settings = get_settings()

        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embedding_provider = embedding_provider or OpenAIEmbeddingProvider()

        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add documents to the vector store"""
        if not documents:
            return []

        # Generate IDs if not provided
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(documents))]

        # Generate embeddings
        embeddings = await self.embedding_provider.get_embeddings(documents)

        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{}] * len(documents),
            ids=ids,
        )

        return ids

    async def search(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        # Get query embedding
        query_embeddings = await self.embedding_provider.get_embeddings([query])

        # Search in collection
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted_results.append(
                    {
                        "content": doc,
                        "metadata": (
                            results["metadatas"][0][i]
                            if results["metadatas"]
                            else {}
                        ),
                        "distance": (
                            results["distances"][0][i]
                            if results["distances"]
                            else 0.0
                        ),
                        "id": results["ids"][0][i] if results["ids"] else None,
                    }
                )

        return formatted_results

    async def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by IDs"""
        if ids:
            self.collection.delete(ids=ids)

    async def update_document(
        self,
        id: str,
        document: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update a document"""
        update_kwargs = {"ids": [id]}

        if document:
            embeddings = await self.embedding_provider.get_embeddings([document])
            update_kwargs["documents"] = [document]
            update_kwargs["embeddings"] = embeddings

        if metadata:
            update_kwargs["metadatas"] = [metadata]

        self.collection.update(**update_kwargs)

    def get_document_count(self) -> int:
        """Get total document count"""
        return self.collection.count()

    def clear_collection(self) -> None:
        """Clear all documents from collection"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
