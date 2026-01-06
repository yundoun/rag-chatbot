"""WebSocket endpoint for HITL communication"""

import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.websocket_manager import (
    WebSocketManager,
    WebSocketMessage,
    MessageType,
    get_websocket_manager,
)
from src.core.orchestrator import get_orchestrator
from src.core.models import RAGResponse, ClarificationOutput

router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat with HITL support

    Message Protocol:
    - Client sends: {"type": "question", "data": {"query": "..."}}
    - Server responds with either:
      - Progress: {"type": "progress", "data": {"step": "...", "progress": 0.5}}
      - Clarification: {"type": "clarification_request", "data": {"question": "...", "options": [...]}}
      - Response: {"type": "response", "data": {"response": "...", "sources": [...], ...}}
      - Error: {"type": "error", "data": {"error": "...", "detail": "..."}}

    HITL Flow:
    1. Client sends question
    2. If clarification needed, server sends clarification_request
    3. Client responds with: {"type": "clarification", "data": {"selected_option": "..."}}
    4. Server continues processing and sends response
    """
    manager = get_websocket_manager()
    orchestrator = get_orchestrator()

    # Generate session ID
    session_id = str(uuid.uuid4())

    # Accept connection
    if not await manager.connect(websocket, session_id):
        return

    try:
        # Send connection confirmation
        await manager.send_message(
            session_id,
            WebSocketMessage(
                type=MessageType.PROGRESS,
                data={"step": "connected", "progress": 0.0, "session_id": session_id},
                session_id=session_id,
            ),
        )

        while True:
            # Wait for client message
            message = await manager.receive_message(session_id)

            if message is None:
                break

            if message.type == MessageType.QUESTION:
                await handle_question(
                    manager=manager,
                    orchestrator=orchestrator,
                    session_id=session_id,
                    query=message.data.get("query", ""),
                )
            elif message.type == MessageType.CLARIFICATION:
                await handle_clarification(
                    manager=manager,
                    orchestrator=orchestrator,
                    session_id=session_id,
                    response_data=message.data,
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await manager.send_error(session_id, "서버 오류가 발생했습니다.", str(e))
    finally:
        await manager.disconnect(session_id)


async def handle_question(
    manager: WebSocketManager,
    orchestrator,
    session_id: str,
    query: str,
):
    """Handle initial question from client"""
    if not query.strip():
        await manager.send_error(session_id, "질문을 입력해 주세요.")
        return

    # Send progress: analyzing
    await manager.send_progress(session_id, "질문 분석 중...", 0.1)

    try:
        # Process query through orchestrator
        result = await orchestrator.process_query(query=query, session_id=session_id)

        if isinstance(result, ClarificationOutput):
            # HITL needed - send clarification request
            await manager.send_progress(session_id, "명확화 필요", 0.3)
            await manager.send_clarification_request(
                session_id=session_id,
                question=result.clarification_question,
                options=result.options,
            )
        elif isinstance(result, RAGResponse):
            # Got final response
            await manager.send_progress(session_id, "답변 완료", 1.0)
            await manager.send_response(
                session_id=session_id,
                response=result.response,
                sources=result.sources,
                confidence=result.confidence,
                needs_disclaimer=result.needs_disclaimer,
                retrieval_source=result.retrieval_source.value,
            )
    except Exception as e:
        await manager.send_error(session_id, "처리 중 오류가 발생했습니다.", str(e))


async def handle_clarification(
    manager: WebSocketManager,
    orchestrator,
    session_id: str,
    response_data: dict,
):
    """Handle clarification response from client"""
    # Get user's response
    user_response = response_data.get("custom_input") or response_data.get("selected_option")

    if not user_response:
        await manager.send_error(session_id, "응답을 선택하거나 입력해 주세요.")
        return

    # Check if there's a pending session
    if not orchestrator.has_pending_session(session_id):
        await manager.send_error(session_id, "세션이 만료되었습니다. 다시 질문해 주세요.")
        return

    # Send progress: processing clarification
    await manager.send_progress(session_id, "응답 처리 중...", 0.5)

    try:
        # Continue processing with user response
        # We need the original query from the pending session
        pending = orchestrator._pending_sessions.get(session_id, {})
        original_query = pending.get("query", "")

        result = await orchestrator.process_query(
            query=original_query,
            session_id=session_id,
            user_response=user_response,
        )

        if isinstance(result, ClarificationOutput):
            # Need another clarification
            await manager.send_progress(session_id, "추가 명확화 필요", 0.6)
            await manager.send_clarification_request(
                session_id=session_id,
                question=result.clarification_question,
                options=result.options,
            )
        elif isinstance(result, RAGResponse):
            # Got final response
            await manager.send_progress(session_id, "답변 완료", 1.0)
            await manager.send_response(
                session_id=session_id,
                response=result.response,
                sources=result.sources,
                confidence=result.confidence,
                needs_disclaimer=result.needs_disclaimer,
                retrieval_source=result.retrieval_source.value,
            )
    except Exception as e:
        await manager.send_error(session_id, "처리 중 오류가 발생했습니다.", str(e))


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat_with_session(websocket: WebSocket, session_id: str):
    """WebSocket endpoint with explicit session ID

    Use this endpoint to reconnect to an existing session or
    start a new session with a specific ID.
    """
    manager = get_websocket_manager()
    orchestrator = get_orchestrator()

    # Accept connection
    if not await manager.connect(websocket, session_id):
        return

    try:
        # Check for pending clarification
        pending = orchestrator.get_pending_clarification(session_id)
        if pending:
            # Resend the clarification request
            await manager.send_clarification_request(
                session_id=session_id,
                question=pending.clarification_question,
                options=pending.options,
            )
        else:
            # Send connection confirmation
            await manager.send_message(
                session_id,
                WebSocketMessage(
                    type=MessageType.PROGRESS,
                    data={"step": "connected", "progress": 0.0, "session_id": session_id},
                    session_id=session_id,
                ),
            )

        while True:
            message = await manager.receive_message(session_id)

            if message is None:
                break

            if message.type == MessageType.QUESTION:
                await handle_question(manager, orchestrator, session_id, message.data.get("query", ""))
            elif message.type == MessageType.CLARIFICATION:
                await handle_clarification(manager, orchestrator, session_id, message.data)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await manager.send_error(session_id, "서버 오류가 발생했습니다.", str(e))
    finally:
        await manager.disconnect(session_id)
