"""Document Indexer for processing and indexing documents"""

import hashlib
import os
from typing import Any, Dict, List, Optional

from src.config import MAX_DOCUMENT_CHUNK_SIZE
from .manager import VectorStoreManager


class DocumentIndexer:
    """Document indexer for chunking and indexing documents"""

    def __init__(
        self,
        vector_store: Optional[VectorStoreManager] = None,
        chunk_size: int = MAX_DOCUMENT_CHUNK_SIZE,
        chunk_overlap: int = 100,
    ):
        self.vector_store = vector_store or VectorStoreManager()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _generate_doc_id(self, content: str, source: str) -> str:
        """Generate unique document ID"""
        hash_input = f"{source}:{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                for punct in [".", "!", "?", "\n"]:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct > start + self.chunk_size // 2:
                        end = last_punct + 1
                        break

            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap

        return [chunk for chunk in chunks if chunk]

    async def index_text(
        self,
        text: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Index a text document with chunking"""
        chunks = self._chunk_text(text)
        base_metadata = metadata or {}
        base_metadata["source"] = source

        documents = []
        metadatas = []
        ids = []

        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **base_metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            doc_id = self._generate_doc_id(chunk, f"{source}_{i}")

            documents.append(chunk)
            metadatas.append(chunk_metadata)
            ids.append(doc_id)

        return await self.vector_store.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    async def index_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Index a file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        file_metadata = metadata or {}
        file_metadata["file_path"] = file_path
        file_metadata["file_name"] = os.path.basename(file_path)

        return await self.index_text(
            text=content,
            source=file_path,
            metadata=file_metadata,
        )

    async def index_directory(
        self,
        directory_path: str,
        extensions: List[str] = [".txt", ".md", ".py"],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[str]]:
        """Index all files in a directory"""
        if not os.path.isdir(directory_path):
            raise NotADirectoryError(f"Not a directory: {directory_path}")

        results = {}

        for root, _, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        ids = await self.index_file(file_path, metadata)
                        results[file_path] = ids
                    except Exception as e:
                        results[file_path] = [f"Error: {str(e)}"]

        return results
