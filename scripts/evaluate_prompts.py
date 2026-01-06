#!/usr/bin/env python3
"""
Prompt Evaluation CLI Tool

Evaluate RAG prompts against test queries and measure quality.

Usage:
    python scripts/evaluate_prompts.py --queries ./data/test_queries.json
    python scripts/evaluate_prompts.py --query "RAG 시스템이란 무엇인가요?"
    python scripts/evaluate_prompts.py --benchmark
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvaluationResult:
    """Result of a single query evaluation"""

    query: str
    response: str
    latency_ms: float
    retrieved_docs: int
    relevance_score: Optional[float] = None
    expected_answer: Optional[str] = None
    similarity_score: Optional[float] = None
    error: Optional[str] = None


@dataclass
class EvaluationSummary:
    """Summary of evaluation results"""

    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_latency_ms: float = 0.0
    avg_relevance_score: float = 0.0
    avg_similarity_score: float = 0.0
    results: List[EvaluationResult] = field(default_factory=list)


class PromptEvaluator:
    """Evaluates RAG prompts and responses"""

    def __init__(self, collection_name: str = "rag-documents"):
        self.collection_name = collection_name
        self._llm = None
        self._embeddings = None
        self._retriever = None

    def _init_components(self):
        """Initialize LLM and retriever"""
        try:
            from langchain_openai import ChatOpenAI, OpenAIEmbeddings
            import chromadb
            from chromadb.config import Settings

            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
                sys.exit(1)

            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                openai_api_key=api_key,
            )

            self._embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key,
            )

            # Initialize ChromaDB
            client = chromadb.PersistentClient(
                path="./data/chroma",
                settings=Settings(anonymized_telemetry=False),
            )

            try:
                self._collection = client.get_collection(self.collection_name)
                print(f"✅ 컬렉션 로드 완료: {self.collection_name}")
                print(f"   문서 수: {self._collection.count()}")
            except Exception:
                print(f"⚠️ 컬렉션을 찾을 수 없습니다: {self.collection_name}")
                print("   먼저 index_documents.py를 실행해 주세요.")
                self._collection = None

            print("✅ 컴포넌트 초기화 완료")

        except ImportError as e:
            print(f"❌ 필요한 패키지가 설치되지 않았습니다: {e}")
            sys.exit(1)

    def _retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        """Retrieve relevant documents"""
        if self._collection is None:
            return []

        try:
            query_embedding = self._embeddings.embed_query(query)

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            docs = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    docs.append(
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
                                else 0
                            ),
                        }
                    )
            return docs

        except Exception as e:
            print(f"  ⚠️ 검색 오류: {e}")
            return []

    def _generate_response(self, query: str, context: str) -> str:
        """Generate response using LLM"""
        prompt = f"""다음 컨텍스트를 기반으로 질문에 답변해 주세요.

컨텍스트:
{context}

질문: {query}

답변:"""

        try:
            response = self._llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"오류: {e}"

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        try:
            emb1 = self._embeddings.embed_query(text1)
            emb2 = self._embeddings.embed_query(text2)

            # Cosine similarity
            import math

            dot_product = sum(a * b for a, b in zip(emb1, emb2))
            norm1 = math.sqrt(sum(a * a for a in emb1))
            norm2 = math.sqrt(sum(b * b for b in emb2))

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0

    def evaluate_query(
        self,
        query: str,
        expected_answer: Optional[str] = None,
        top_k: int = 5,
    ) -> EvaluationResult:
        """Evaluate a single query"""
        start_time = time.perf_counter()

        try:
            # Retrieve documents
            docs = self._retrieve(query, top_k)

            if not docs:
                return EvaluationResult(
                    query=query,
                    response="",
                    latency_ms=0,
                    retrieved_docs=0,
                    error="검색 결과 없음",
                )

            # Build context
            context = "\n\n".join([d["content"] for d in docs])

            # Calculate average relevance score
            avg_relevance = 1 - (sum(d["distance"] for d in docs) / len(docs))

            # Generate response
            response = self._generate_response(query, context)

            latency_ms = (time.perf_counter() - start_time) * 1000

            result = EvaluationResult(
                query=query,
                response=response,
                latency_ms=latency_ms,
                retrieved_docs=len(docs),
                relevance_score=avg_relevance,
                expected_answer=expected_answer,
            )

            # Calculate similarity if expected answer provided
            if expected_answer:
                result.similarity_score = self._calculate_similarity(
                    response, expected_answer
                )

            return result

        except Exception as e:
            return EvaluationResult(
                query=query,
                response="",
                latency_ms=(time.perf_counter() - start_time) * 1000,
                retrieved_docs=0,
                error=str(e),
            )

    def evaluate_queries(
        self,
        queries: List[Dict],
        top_k: int = 5,
    ) -> EvaluationSummary:
        """Evaluate multiple queries"""
        self._init_components()

        summary = EvaluationSummary()
        summary.total_queries = len(queries)

        print(f"\n🔍 {len(queries)}개 쿼리 평가 시작")
        print("=" * 50)

        for i, query_data in enumerate(queries, 1):
            query = query_data.get("query", query_data) if isinstance(query_data, dict) else query_data
            expected = query_data.get("expected") if isinstance(query_data, dict) else None

            print(f"\n[{i}/{len(queries)}] 평가 중: {query[:50]}...")

            result = self.evaluate_query(query, expected, top_k)
            summary.results.append(result)

            if result.error:
                summary.failed_queries += 1
                print(f"  ❌ 실패: {result.error}")
            else:
                summary.successful_queries += 1
                print(f"  ✅ 성공 - 지연: {result.latency_ms:.0f}ms, 문서: {result.retrieved_docs}")
                if result.relevance_score:
                    print(f"     관련성: {result.relevance_score:.2f}")
                if result.similarity_score:
                    print(f"     유사도: {result.similarity_score:.2f}")

        # Calculate averages
        successful = [r for r in summary.results if not r.error]
        if successful:
            summary.avg_latency_ms = sum(r.latency_ms for r in successful) / len(successful)

            relevance_scores = [r.relevance_score for r in successful if r.relevance_score]
            if relevance_scores:
                summary.avg_relevance_score = sum(relevance_scores) / len(relevance_scores)

            similarity_scores = [r.similarity_score for r in successful if r.similarity_score]
            if similarity_scores:
                summary.avg_similarity_score = sum(similarity_scores) / len(similarity_scores)

        return summary

    def run_benchmark(self) -> EvaluationSummary:
        """Run benchmark with predefined test queries"""
        benchmark_queries = [
            {
                "query": "RAG 시스템의 주요 구성 요소는 무엇인가요?",
                "expected": "RAG 시스템은 검색(Retrieval), 증강(Augmentation), 생성(Generation) 세 가지 주요 구성 요소로 이루어져 있습니다.",
            },
            {
                "query": "벡터 데이터베이스란 무엇인가요?",
                "expected": "벡터 데이터베이스는 고차원 벡터 데이터를 저장하고 유사성 검색을 수행하는 데 최적화된 데이터베이스입니다.",
            },
            {
                "query": "임베딩이란 무엇인가요?",
                "expected": "임베딩은 텍스트나 다른 데이터를 고차원 벡터 공간에 매핑하는 것으로, 의미적 유사성을 수치로 표현합니다.",
            },
            {
                "query": "LangChain의 주요 기능은?",
                "expected": "LangChain은 LLM 애플리케이션 개발을 위한 프레임워크로, 체인, 에이전트, 메모리 등의 기능을 제공합니다.",
            },
            {
                "query": "프롬프트 엔지니어링이란?",
                "expected": "프롬프트 엔지니어링은 LLM에서 원하는 출력을 얻기 위해 입력 프롬프트를 설계하고 최적화하는 기술입니다.",
            },
        ]

        print("\n🏁 벤치마크 실행")
        return self.evaluate_queries(benchmark_queries)


def print_summary(summary: EvaluationSummary):
    """Print evaluation summary"""
    print("\n" + "=" * 50)
    print("📊 평가 결과 요약")
    print("=" * 50)
    print(f"  총 쿼리 수: {summary.total_queries}")
    print(f"  성공: {summary.successful_queries}")
    print(f"  실패: {summary.failed_queries}")
    print(f"  평균 지연 시간: {summary.avg_latency_ms:.0f}ms")
    print(f"  평균 관련성 점수: {summary.avg_relevance_score:.2f}")

    if summary.avg_similarity_score > 0:
        print(f"  평균 유사도 점수: {summary.avg_similarity_score:.2f}")

    # Quality assessment
    print("\n📈 품질 평가:")
    if summary.avg_relevance_score >= 0.8:
        print("  ✅ 관련성: 우수")
    elif summary.avg_relevance_score >= 0.6:
        print("  ⚠️ 관련성: 양호")
    else:
        print("  ❌ 관련성: 개선 필요")

    if summary.avg_latency_ms <= 2000:
        print("  ✅ 응답 속도: 우수")
    elif summary.avg_latency_ms <= 5000:
        print("  ⚠️ 응답 속도: 양호")
    else:
        print("  ❌ 응답 속도: 개선 필요")


def save_results(summary: EvaluationSummary, output_path: str):
    """Save evaluation results to JSON"""
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_queries": summary.total_queries,
            "successful_queries": summary.successful_queries,
            "failed_queries": summary.failed_queries,
            "avg_latency_ms": summary.avg_latency_ms,
            "avg_relevance_score": summary.avg_relevance_score,
            "avg_similarity_score": summary.avg_similarity_score,
        },
        "results": [
            {
                "query": r.query,
                "response": r.response,
                "latency_ms": r.latency_ms,
                "retrieved_docs": r.retrieved_docs,
                "relevance_score": r.relevance_score,
                "similarity_score": r.similarity_score,
                "expected_answer": r.expected_answer,
                "error": r.error,
            }
            for r in summary.results
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 결과 저장됨: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="프롬프트 평가 CLI 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python scripts/evaluate_prompts.py --benchmark
  python scripts/evaluate_prompts.py --query "RAG란 무엇인가요?"
  python scripts/evaluate_prompts.py --queries ./test_queries.json --output ./results.json
        """,
    )

    parser.add_argument(
        "--query",
        type=str,
        help="단일 쿼리 평가",
    )
    parser.add_argument(
        "--queries",
        type=str,
        help="쿼리 파일 경로 (JSON)",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="rag-documents",
        help="ChromaDB 컬렉션 이름",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="검색할 문서 수 (기본: 5)",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="벤치마크 실행",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="결과 저장 경로 (JSON)",
    )

    args = parser.parse_args()

    evaluator = PromptEvaluator(collection_name=args.collection)

    if args.benchmark:
        summary = evaluator.run_benchmark()
    elif args.query:
        evaluator._init_components()
        print(f"\n🔍 쿼리 평가: {args.query}")
        result = evaluator.evaluate_query(args.query, top_k=args.top_k)

        if result.error:
            print(f"❌ 오류: {result.error}")
        else:
            print(f"\n📝 응답:\n{result.response}")
            print(f"\n⏱️ 지연 시간: {result.latency_ms:.0f}ms")
            print(f"📚 검색된 문서: {result.retrieved_docs}")
            if result.relevance_score:
                print(f"📊 관련성 점수: {result.relevance_score:.2f}")
        return
    elif args.queries:
        with open(args.queries, "r", encoding="utf-8") as f:
            queries = json.load(f)
        summary = evaluator.evaluate_queries(queries, top_k=args.top_k)
    else:
        parser.error("--query, --queries, 또는 --benchmark 옵션이 필요합니다")

    print_summary(summary)

    if args.output:
        save_results(summary, args.output)


if __name__ == "__main__":
    main()
