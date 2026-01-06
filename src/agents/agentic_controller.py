"""Agentic Controller for complex query decomposition and parallel retrieval"""

import asyncio
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from src.config import get_settings
from src.core.models import Document, Complexity
from src.llm import get_llm_provider
from src.llm.prompts.decomposition import (
    QUERY_DECOMPOSITION_PROMPT,
    SUB_ANSWER_SYNTHESIS_PROMPT,
)


class SubQuestion(BaseModel):
    """A decomposed sub-question"""
    id: str
    question: str
    target_domain: str = ""
    dependencies: List[str] = []


class DecompositionResult(BaseModel):
    """Result of query decomposition"""
    original_intent: str
    sub_questions: List[SubQuestion]
    parallel_groups: List[List[str]] = []
    synthesis_guide: str = ""


class SynthesisResult(BaseModel):
    """Result of answer synthesis"""
    synthesized_response: str
    sources: List[str] = []
    coverage_score: float = Field(ge=0.0, le=1.0, default=0.0)
    inconsistencies: List[str] = []


class SubAnswer(BaseModel):
    """An answer to a sub-question"""
    question_id: str
    question: str
    answer: str
    sources: List[str] = []
    confidence: float = 0.0


class AgenticController:
    """Controller for decomposing complex queries and orchestrating parallel retrieval"""

    def __init__(self, llm_provider=None):
        self.llm = llm_provider or get_llm_provider()
        self.settings = get_settings()

    def should_decompose(self, complexity: str) -> bool:
        """Determine if query should be decomposed

        Args:
            complexity: Query complexity from analysis ('simple' or 'complex')

        Returns:
            True if decomposition is needed
        """
        return complexity == "complex"

    async def decompose_query(
        self,
        query: str,
        complexity: str,
        detected_domains: Optional[List[str]] = None,
    ) -> DecompositionResult:
        """Decompose a complex query into sub-questions

        Args:
            query: The original complex query
            complexity: Complexity level
            detected_domains: Domains detected in the query

        Returns:
            DecompositionResult with sub-questions and execution plan
        """
        prompt = QUERY_DECOMPOSITION_PROMPT.format(
            query=query,
            complexity=complexity,
            detected_domains=", ".join(detected_domains) if detected_domains else "없음",
        )

        try:
            result = await self.llm.generate_structured(
                prompt=prompt,
                output_schema=DecompositionResult,
            )

            # Validate sub-questions
            if not result.sub_questions or len(result.sub_questions) < 2:
                return self._create_simple_decomposition(query)

            # Ensure parallel groups are valid
            if not result.parallel_groups:
                result.parallel_groups = self._create_default_parallel_groups(
                    result.sub_questions
                )

            return result
        except Exception:
            return self._create_simple_decomposition(query)

    async def execute_parallel_retrieval(
        self,
        decomposition: DecompositionResult,
        retrieval_func,
    ) -> List[SubAnswer]:
        """Execute retrieval for sub-questions respecting dependencies

        Args:
            decomposition: The decomposition result
            retrieval_func: Async function to retrieve and generate answer
                           Signature: async def(query: str, domain: str) -> Tuple[str, List[str], float]

        Returns:
            List of SubAnswer objects
        """
        sub_answers = []
        completed_ids = set()
        question_map = {q.id: q for q in decomposition.sub_questions}

        for group in decomposition.parallel_groups:
            # Filter questions whose dependencies are met
            executable = [
                qid for qid in group
                if qid in question_map
                and all(dep in completed_ids for dep in question_map[qid].dependencies)
            ]

            if not executable:
                continue

            # Execute in parallel
            tasks = []
            for qid in executable:
                q = question_map[qid]
                tasks.append(self._execute_single_retrieval(q, retrieval_func))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for qid, result in zip(executable, results):
                if isinstance(result, Exception):
                    # Create error answer
                    sub_answers.append(SubAnswer(
                        question_id=qid,
                        question=question_map[qid].question,
                        answer="정보를 찾을 수 없습니다.",
                        sources=[],
                        confidence=0.0,
                    ))
                else:
                    sub_answers.append(result)
                completed_ids.add(qid)

        return sub_answers

    async def _execute_single_retrieval(
        self,
        question: SubQuestion,
        retrieval_func,
    ) -> SubAnswer:
        """Execute retrieval for a single sub-question"""
        try:
            answer, sources, confidence = await retrieval_func(
                question.question,
                question.target_domain,
            )
            return SubAnswer(
                question_id=question.id,
                question=question.question,
                answer=answer,
                sources=sources,
                confidence=confidence,
            )
        except Exception as e:
            return SubAnswer(
                question_id=question.id,
                question=question.question,
                answer=f"오류 발생: {str(e)}",
                sources=[],
                confidence=0.0,
            )

    async def synthesize_answers(
        self,
        original_query: str,
        sub_answers: List[SubAnswer],
        synthesis_guide: str,
    ) -> SynthesisResult:
        """Synthesize sub-answers into a coherent response

        Args:
            original_query: The original user query
            sub_answers: List of sub-question answers
            synthesis_guide: Guide for synthesis from decomposition

        Returns:
            SynthesisResult with combined answer
        """
        # Format sub-answers for prompt
        formatted_answers = []
        for sa in sub_answers:
            formatted_answers.append(
                f"질문: {sa.question}\n"
                f"답변: {sa.answer}\n"
                f"출처: {', '.join(sa.sources) if sa.sources else '없음'}\n"
                f"신뢰도: {sa.confidence:.2f}"
            )

        prompt = SUB_ANSWER_SYNTHESIS_PROMPT.format(
            original_query=original_query,
            sub_answers="\n\n---\n\n".join(formatted_answers),
            synthesis_guide=synthesis_guide or "논리적 순서로 답변을 결합하세요.",
        )

        try:
            result = await self.llm.generate_structured(
                prompt=prompt,
                output_schema=SynthesisResult,
            )

            # Collect all sources
            all_sources = set()
            for sa in sub_answers:
                all_sources.update(sa.sources)
            result.sources = list(all_sources)

            return result
        except Exception:
            # Fallback: simple concatenation
            combined = "\n\n".join([
                f"**{sa.question}**\n{sa.answer}"
                for sa in sub_answers
            ])
            all_sources = []
            for sa in sub_answers:
                all_sources.extend(sa.sources)

            return SynthesisResult(
                synthesized_response=combined,
                sources=list(set(all_sources)),
                coverage_score=0.5,
                inconsistencies=[],
            )

    def _create_simple_decomposition(self, query: str) -> DecompositionResult:
        """Create a simple decomposition for fallback"""
        return DecompositionResult(
            original_intent=query,
            sub_questions=[
                SubQuestion(
                    id="q1",
                    question=query,
                    target_domain="",
                    dependencies=[],
                )
            ],
            parallel_groups=[["q1"]],
            synthesis_guide="단일 질문 - 직접 답변 사용",
        )

    def _create_default_parallel_groups(
        self,
        sub_questions: List[SubQuestion],
    ) -> List[List[str]]:
        """Create default parallel groups based on dependencies"""
        groups = []
        processed = set()

        # First, find all questions with no dependencies
        no_deps = [q.id for q in sub_questions if not q.dependencies]
        if no_deps:
            groups.append(no_deps)
            processed.update(no_deps)

        # Then process remaining questions level by level
        remaining = [q for q in sub_questions if q.id not in processed]
        while remaining:
            # Find questions whose dependencies are all processed
            ready = [
                q.id for q in remaining
                if all(dep in processed for dep in q.dependencies)
            ]

            if not ready:
                # Circular dependency or error - add all remaining
                groups.append([q.id for q in remaining])
                break

            groups.append(ready)
            processed.update(ready)
            remaining = [q for q in remaining if q.id not in processed]

        return groups


# Factory function
def get_agentic_controller() -> AgenticController:
    """Get agentic controller instance"""
    return AgenticController()
