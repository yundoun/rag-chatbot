"""Chat API routes with Corrective RAG and HITL support"""

import uuid
from datetime import datetime
from typing import Optional, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import get_settings
from src.core.models import (
    RAGRequest,
    RAGResponse,
    ClarificationOutput,
    RetrievalSource,
)
from src.core.exceptions import (
    RAGException,
    ValidationException,
)
from src.core.orchestrator import get_orchestrator


router = APIRouter()


class ClarificationRequest(BaseModel):
    """Request to continue with clarification response"""
    session_id: str
    user_response: str


class ChatResponse(BaseModel):
    """Combined response that can be either RAGResponse or ClarificationOutput"""
    # RAG Response fields
    response: Optional[str] = None
    sources: list = []
    confidence: float = 0.0
    needs_disclaimer: bool = False
    retrieval_source: Optional[str] = None
    processing_time_ms: int = 0
    session_id: str
    debug: Optional[dict] = None

    # Clarification fields
    clarification_question: Optional[str] = None
    options: Optional[list] = None

    # Meta
    needs_clarification: bool = False


@router.post("/chat", response_model=ChatResponse)
async def chat(request: RAGRequest):
    """
    Process a chat query through the Corrective RAG pipeline with HITL support

    Pipeline:
    1. Query analysis (complexity, clarity, domains)
    2. HITL clarification if ambiguous (returns clarification_question)
    3. Document retrieval from vector store
    4. Relevance evaluation
    5. Query rewriting if needed (up to 2 retries)
    6. Web search fallback if relevance still low
    7. Response generation with source citations
    8. Quality evaluation and disclaimer decision
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Get the LangGraph orchestrator
        orchestrator = get_orchestrator()

        # Process query through the full RAG pipeline
        result = await orchestrator.process_query(
            query=request.query,
            session_id=session_id,
        )

        # Check if clarification is needed
        if isinstance(result, ClarificationOutput):
            return ChatResponse(
                session_id=session_id,
                needs_clarification=True,
                clarification_question=result.clarification_question,
                options=result.options,
            )

        # Return normal response
        return ChatResponse(
            response=result.response,
            sources=result.sources,
            confidence=result.confidence,
            needs_disclaimer=result.needs_disclaimer,
            retrieval_source=result.retrieval_source.value,
            processing_time_ms=result.processing_time_ms,
            session_id=result.session_id,
            debug=result.debug,
            needs_clarification=False,
        )

    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RAGException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/chat/clarify", response_model=ChatResponse)
async def chat_clarify(request: ClarificationRequest):
    """
    Continue a chat session with a clarification response

    Used when the previous /chat request returned needs_clarification=true.
    The user's response is processed and the pipeline continues.
    """
    try:
        orchestrator = get_orchestrator()

        # Check if there's a pending session
        if not orchestrator.has_pending_session(request.session_id):
            raise HTTPException(
                status_code=400,
                detail="세션이 만료되었습니다. 새로운 질문을 입력해 주세요.",
            )

        # Get the original query from pending session
        pending_state = orchestrator._pending_sessions.get(request.session_id, {})
        original_query = pending_state.get("query", "")

        # Continue processing with user response
        result = await orchestrator.process_query(
            query=original_query,
            session_id=request.session_id,
            user_response=request.user_response,
        )

        # Check if another clarification is needed
        if isinstance(result, ClarificationOutput):
            return ChatResponse(
                session_id=request.session_id,
                needs_clarification=True,
                clarification_question=result.clarification_question,
                options=result.options,
            )

        # Return normal response
        return ChatResponse(
            response=result.response,
            sources=result.sources,
            confidence=result.confidence,
            needs_disclaimer=result.needs_disclaimer,
            retrieval_source=result.retrieval_source.value,
            processing_time_ms=result.processing_time_ms,
            session_id=result.session_id,
            debug=result.debug,
            needs_clarification=False,
        )

    except HTTPException:
        raise
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RAGException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/chat/simple", response_model=RAGResponse)
async def chat_simple(request: RAGRequest):
    """
    Simple chat endpoint without corrective RAG (for comparison/fallback)

    Uses basic retrieve-generate flow without correction loop.
    """
    import time
    from src.agents import QueryProcessor
    from src.rag import DocumentRetriever, ResponseGenerator
    from src.core.exceptions import NoResultsException

    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Initialize components
        query_processor = QueryProcessor()
        retriever = DocumentRetriever()
        response_generator = ResponseGenerator()

        # Step 1: Analyze query
        analysis = await query_processor.analyze(request.query)

        # Step 2: Retrieve documents
        query_to_search = analysis.refined_query or request.query

        try:
            documents = await retriever.retrieve(
                query=query_to_search,
                domains=analysis.detected_domains if analysis.detected_domains else None,
            )
        except NoResultsException:
            processing_time = int((time.time() - start_time) * 1000)
            return RAGResponse(
                response="관련 문서를 찾을 수 없습니다. 다른 키워드로 다시 검색해 주세요.",
                sources=[],
                confidence=0.0,
                needs_disclaimer=True,
                retrieval_source=RetrievalSource.VECTOR,
                processing_time_ms=processing_time,
                session_id=session_id,
            )

        # Step 3: Calculate relevance metrics
        metrics = retriever.calculate_relevance_metrics(documents)

        # Step 4: Generate response
        response = await response_generator.generate(
            query=request.query,
            documents=documents,
        )

        # Calculate confidence
        confidence = response_generator.evaluate_response_quality(response, documents)
        needs_disclaimer = confidence < 0.6 or not response.has_sufficient_info

        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)

        return RAGResponse(
            response=response.response,
            sources=response.sources,
            confidence=confidence,
            needs_disclaimer=needs_disclaimer,
            retrieval_source=RetrievalSource.VECTOR,
            processing_time_ms=processing_time,
            session_id=session_id,
            debug={
                "mode": "simple",
                "query_analysis": {
                    "complexity": analysis.complexity.value,
                    "clarity_confidence": analysis.clarity_confidence,
                    "is_ambiguous": analysis.is_ambiguous,
                    "detected_domains": analysis.detected_domains,
                },
                "retrieval_metrics": metrics,
            } if get_settings().debug else None,
        )

    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RAGException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/chat/sessions/{session_id}")
async def get_session(session_id: str):
    """Get chat session info (placeholder for future session management)"""
    return {
        "session_id": session_id,
        "status": "active",
        "created_at": datetime.now(),
    }
