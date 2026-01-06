#!/usr/bin/env python3
"""
Document Indexing CLI Tool

Batch index markdown documents into ChromaDB vector store.

Usage:
    python scripts/index_documents.py --source ./data/docs --collection rag-docs
    python scripts/index_documents.py --source ./data/docs --reset
    python scripts/index_documents.py --status
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DocumentChunk:
    """Represents a document chunk for indexing"""

    content: str
    metadata: dict
    doc_id: str


@dataclass
class IndexingStats:
    """Statistics for indexing operation"""

    total_files: int = 0
    processed_files: int = 0
    total_chunks: int = 0
    skipped_files: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DocumentIndexer:
    """Indexes markdown documents into ChromaDB"""

    def __init__(
        self,
        collection_name: str = "documents",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        persist_directory: str = "./data/chroma_db",
    ):
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None
        self._embeddings = None

    def _init_chromadb(self):
        """Initialize ChromaDB client"""
        try:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            print(f"✅ ChromaDB 초기화 완료: {self.collection_name}")
        except ImportError:
            print("❌ chromadb 패키지가 설치되지 않았습니다.")
            print("   pip install chromadb")
            sys.exit(1)
        except Exception as e:
            print(f"❌ ChromaDB 초기화 실패: {e}")
            sys.exit(1)

    def _init_embeddings(self):
        """Initialize embedding model"""
        try:
            from langchain_openai import OpenAIEmbeddings

            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
                sys.exit(1)

            self._embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key,
            )
            print("✅ 임베딩 모델 초기화 완료")
        except ImportError:
            print("❌ langchain-openai 패키지가 설치되지 않았습니다.")
            print("   pip install langchain-openai")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 임베딩 모델 초기화 실패: {e}")
            sys.exit(1)

    def _read_markdown_file(self, file_path: Path) -> Optional[str]:
        """Read markdown file content"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"  ⚠️ 파일 읽기 실패: {file_path} - {e}")
            return None

    def _chunk_text(self, text: str, file_path: Path) -> List[DocumentChunk]:
        """Split text into chunks with metadata"""
        chunks = []
        file_name = file_path.stem
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]

        # Simple chunking by paragraphs first, then by size
        paragraphs = text.split("\n\n")
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(
                        self._create_chunk(
                            current_chunk.strip(),
                            file_path,
                            file_hash,
                            chunk_index,
                        )
                    )
                    chunk_index += 1

                # Handle large paragraphs
                if len(para) > self.chunk_size:
                    # Split by sentences or fixed size
                    for i in range(0, len(para), self.chunk_size - self.chunk_overlap):
                        chunk_text = para[i : i + self.chunk_size]
                        if chunk_text.strip():
                            chunks.append(
                                self._create_chunk(
                                    chunk_text.strip(),
                                    file_path,
                                    file_hash,
                                    chunk_index,
                                )
                            )
                            chunk_index += 1
                    current_chunk = ""
                else:
                    current_chunk = para + "\n\n"

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(
                self._create_chunk(
                    current_chunk.strip(),
                    file_path,
                    file_hash,
                    chunk_index,
                )
            )

        return chunks

    def _create_chunk(
        self,
        content: str,
        file_path: Path,
        file_hash: str,
        chunk_index: int,
    ) -> DocumentChunk:
        """Create a document chunk with metadata"""
        doc_id = f"{file_hash}_{chunk_index}"

        return DocumentChunk(
            content=content,
            metadata={
                "source": str(file_path),
                "file_name": file_path.name,
                "chunk_index": chunk_index,
                "indexed_at": datetime.utcnow().isoformat(),
            },
            doc_id=doc_id,
        )

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts"""
        try:
            return self._embeddings.embed_documents(texts)
        except Exception as e:
            print(f"  ⚠️ 임베딩 생성 실패: {e}")
            return []

    def index_directory(
        self,
        source_dir: str,
        reset: bool = False,
        batch_size: int = 100,
    ) -> IndexingStats:
        """
        Index all markdown files in directory.

        Args:
            source_dir: Directory containing markdown files
            reset: Whether to reset collection before indexing
            batch_size: Number of documents to process at once

        Returns:
            Indexing statistics
        """
        stats = IndexingStats()
        source_path = Path(source_dir)

        if not source_path.exists():
            print(f"❌ 디렉토리를 찾을 수 없습니다: {source_dir}")
            return stats

        # Initialize components
        self._init_chromadb()
        self._init_embeddings()

        # Reset collection if requested
        if reset:
            print("🗑️ 기존 컬렉션 삭제 중...")
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = self._client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                print("✅ 컬렉션 초기화 완료")
            except Exception as e:
                print(f"⚠️ 컬렉션 초기화 중 오류: {e}")

        # Find markdown files
        md_files = list(source_path.glob("**/*.md"))
        stats.total_files = len(md_files)

        if not md_files:
            print(f"⚠️ 마크다운 파일을 찾을 수 없습니다: {source_dir}")
            return stats

        print(f"\n📁 {stats.total_files}개의 마크다운 파일 발견")
        print("=" * 50)

        all_chunks: List[DocumentChunk] = []

        # Process each file
        for i, file_path in enumerate(md_files, 1):
            print(f"\n[{i}/{stats.total_files}] 처리 중: {file_path.name}")

            content = self._read_markdown_file(file_path)
            if content is None:
                stats.skipped_files += 1
                stats.errors.append(f"읽기 실패: {file_path}")
                continue

            # Skip empty files
            if not content.strip():
                print(f"  ⏭️ 빈 파일 건너뜀")
                stats.skipped_files += 1
                continue

            chunks = self._chunk_text(content, file_path)
            print(f"  📄 {len(chunks)}개 청크 생성")

            all_chunks.extend(chunks)
            stats.processed_files += 1

        # Index chunks in batches
        if all_chunks:
            print(f"\n🔄 {len(all_chunks)}개 청크 인덱싱 중...")
            print("=" * 50)

            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i : i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(all_chunks) + batch_size - 1) // batch_size

                print(f"  배치 [{batch_num}/{total_batches}] 처리 중...")

                try:
                    texts = [c.content for c in batch]
                    embeddings = self._get_embeddings(texts)

                    if embeddings:
                        self._collection.add(
                            ids=[c.doc_id for c in batch],
                            documents=texts,
                            embeddings=embeddings,
                            metadatas=[c.metadata for c in batch],
                        )
                        stats.total_chunks += len(batch)
                        print(f"    ✅ {len(batch)}개 청크 인덱싱 완료")
                    else:
                        print(f"    ⚠️ 임베딩 생성 실패로 배치 건너뜀")
                        stats.errors.append(f"배치 {batch_num} 임베딩 실패")

                except Exception as e:
                    print(f"    ❌ 배치 인덱싱 실패: {e}")
                    stats.errors.append(f"배치 {batch_num} 인덱싱 실패: {e}")

        return stats

    def get_status(self) -> dict:
        """Get collection status"""
        self._init_chromadb()

        try:
            count = self._collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
            }
        except Exception as e:
            return {"error": str(e)}


def print_stats(stats: IndexingStats):
    """Print indexing statistics"""
    print("\n" + "=" * 50)
    print("📊 인덱싱 결과")
    print("=" * 50)
    print(f"  총 파일 수: {stats.total_files}")
    print(f"  처리된 파일: {stats.processed_files}")
    print(f"  건너뛴 파일: {stats.skipped_files}")
    print(f"  생성된 청크: {stats.total_chunks}")

    if stats.errors:
        print(f"\n⚠️ 오류 ({len(stats.errors)}건):")
        for error in stats.errors[:5]:
            print(f"  - {error}")
        if len(stats.errors) > 5:
            print(f"  ... 외 {len(stats.errors) - 5}건")


def main():
    parser = argparse.ArgumentParser(
        description="문서 인덱싱 CLI 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python scripts/index_documents.py --source ./data/docs
  python scripts/index_documents.py --source ./data/docs --reset
  python scripts/index_documents.py --status
        """,
    )

    parser.add_argument(
        "--source",
        type=str,
        help="마크다운 문서 디렉토리 경로",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="documents",
        help="ChromaDB 컬렉션 이름 (기본: documents)",
    )
    parser.add_argument(
        "--persist-dir",
        type=str,
        default="./data/chroma_db",
        help="ChromaDB 저장 경로 (기본: ./data/chroma_db)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="청크 크기 (기본: 1000자)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="청크 오버랩 (기본: 200자)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="배치 크기 (기본: 100)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="인덱싱 전 컬렉션 초기화",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="컬렉션 상태 확인",
    )

    args = parser.parse_args()

    indexer = DocumentIndexer(
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        persist_directory=args.persist_dir,
    )

    if args.status:
        print("\n📊 컬렉션 상태")
        print("=" * 50)
        status = indexer.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        return

    if not args.source:
        parser.error("--source 또는 --status 옵션이 필요합니다")

    print("\n🚀 문서 인덱싱 시작")
    print("=" * 50)
    print(f"  소스 디렉토리: {args.source}")
    print(f"  컬렉션: {args.collection}")
    print(f"  청크 크기: {args.chunk_size}")
    print(f"  초기화 모드: {'예' if args.reset else '아니오'}")

    stats = indexer.index_directory(
        source_dir=args.source,
        reset=args.reset,
        batch_size=args.batch_size,
    )

    print_stats(stats)

    if stats.total_chunks > 0:
        print("\n✅ 인덱싱 완료!")
    else:
        print("\n⚠️ 인덱싱된 문서가 없습니다.")


if __name__ == "__main__":
    main()
