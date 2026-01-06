"""WebSocket connection manager for HITL communication"""

import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from fastapi import WebSocket
from pydantic import BaseModel


class MessageType(str, Enum):
    """WebSocket message types"""
    # Client -> Server
    QUESTION = "question"  # User's initial question
    CLARIFICATION = "clarification"  # User's clarification response

    # Server -> Client
    RESPONSE = "response"  # Final answer
    ANSWER = "answer"  # Same as response (alias)
    PROGRESS = "progress"  # Processing progress update
    CLARIFICATION_REQUEST = "clarification_request"  # Ask for clarification
    ERROR = "error"  # Error message


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: MessageType
    data: Dict[str, Any]
    session_id: Optional[str] = None
    timestamp: datetime = None

    def __init__(self, **data):
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.now()
        super().__init__(**data)


class ConnectionState(BaseModel):
    """State of a WebSocket connection"""
    session_id: str
    connected_at: datetime
    last_activity: datetime
    pending_clarification: bool = False
    interaction_count: int = 0


class WebSocketManager:
    """Manager for WebSocket connections and HITL sessions"""

    # Connection timeout in seconds
    CONNECTION_TIMEOUT = 300  # 5 minutes

    def __init__(self):
        # Active connections: session_id -> WebSocket
        self._connections: Dict[str, WebSocket] = {}
        # Connection states: session_id -> ConnectionState
        self._states: Dict[str, ConnectionState] = {}
        # Message queues for pending responses
        self._message_queues: Dict[str, asyncio.Queue] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """Accept a new WebSocket connection

        Args:
            websocket: The WebSocket connection
            session_id: Session identifier

        Returns:
            True if connection successful
        """
        try:
            await websocket.accept()

            self._connections[session_id] = websocket
            self._states[session_id] = ConnectionState(
                session_id=session_id,
                connected_at=datetime.now(),
                last_activity=datetime.now(),
            )
            self._message_queues[session_id] = asyncio.Queue()

            return True
        except Exception:
            return False

    async def disconnect(self, session_id: str):
        """Disconnect a WebSocket connection

        Args:
            session_id: Session identifier
        """
        if session_id in self._connections:
            try:
                await self._connections[session_id].close()
            except Exception:
                pass
            del self._connections[session_id]

        if session_id in self._states:
            del self._states[session_id]

        if session_id in self._message_queues:
            del self._message_queues[session_id]

    def is_connected(self, session_id: str) -> bool:
        """Check if session is connected"""
        return session_id in self._connections

    async def send_message(self, session_id: str, message: WebSocketMessage):
        """Send a message to a client

        Args:
            session_id: Target session
            message: Message to send
        """
        if session_id not in self._connections:
            return

        websocket = self._connections[session_id]
        try:
            await websocket.send_json(message.model_dump(mode="json"))
            self._update_activity(session_id)
        except Exception:
            await self.disconnect(session_id)

    async def send_progress(self, session_id: str, step: str, progress: float):
        """Send progress update

        Args:
            session_id: Target session
            step: Current processing step
            progress: Progress percentage (0.0-1.0)
        """
        message = WebSocketMessage(
            type=MessageType.PROGRESS,
            data={"step": step, "progress": progress},
            session_id=session_id,
        )
        await self.send_message(session_id, message)

    async def send_clarification_request(
        self,
        session_id: str,
        question: str,
        options: List[str],
    ):
        """Send clarification request to client

        Args:
            session_id: Target session
            question: Clarification question
            options: Available options
        """
        if session_id in self._states:
            self._states[session_id].pending_clarification = True
            self._states[session_id].interaction_count += 1

        message = WebSocketMessage(
            type=MessageType.CLARIFICATION_REQUEST,
            data={
                "question": question,
                "options": options,
                "allow_custom_input": True,
            },
            session_id=session_id,
        )
        await self.send_message(session_id, message)

    async def send_response(
        self,
        session_id: str,
        response: str,
        sources: List[str],
        confidence: float,
        needs_disclaimer: bool = False,
        retrieval_source: str = "vector",
    ):
        """Send final response to client

        Args:
            session_id: Target session
            response: Generated response text
            sources: List of sources
            confidence: Confidence score
            needs_disclaimer: Whether disclaimer is needed
            retrieval_source: Source of retrieval (vector/web/hybrid)
        """
        if session_id in self._states:
            self._states[session_id].pending_clarification = False

        message = WebSocketMessage(
            type=MessageType.RESPONSE,
            data={
                "response": response,
                "sources": sources,
                "confidence": confidence,
                "needs_disclaimer": needs_disclaimer,
                "retrieval_source": retrieval_source,
            },
            session_id=session_id,
        )
        await self.send_message(session_id, message)

    async def send_error(self, session_id: str, error: str, detail: Optional[str] = None):
        """Send error message to client

        Args:
            session_id: Target session
            error: Error message
            detail: Optional detailed error info
        """
        message = WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": error, "detail": detail},
            session_id=session_id,
        )
        await self.send_message(session_id, message)

    async def receive_message(self, session_id: str, timeout: float = None) -> Optional[WebSocketMessage]:
        """Receive a message from client

        Args:
            session_id: Source session
            timeout: Optional timeout in seconds

        Returns:
            Received message or None if timeout/disconnected
        """
        if session_id not in self._connections:
            return None

        websocket = self._connections[session_id]
        try:
            if timeout:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=timeout,
                )
            else:
                data = await websocket.receive_json()

            self._update_activity(session_id)

            return WebSocketMessage(
                type=MessageType(data.get("type", "question")),
                data=data.get("data", {}),
                session_id=session_id,
            )
        except asyncio.TimeoutError:
            return None
        except Exception:
            await self.disconnect(session_id)
            return None

    async def wait_for_clarification_response(
        self,
        session_id: str,
        timeout: float = 120.0,
    ) -> Optional[str]:
        """Wait for user's clarification response

        Args:
            session_id: Session to wait for
            timeout: Timeout in seconds

        Returns:
            User's response string or None if timeout
        """
        message = await self.receive_message(session_id, timeout=timeout)

        if message is None:
            return None

        if message.type == MessageType.CLARIFICATION:
            data = message.data
            # Check for custom input first
            if data.get("custom_input"):
                return data["custom_input"]
            # Then check for selected option
            if data.get("selected_option"):
                return data["selected_option"]

        return None

    def _update_activity(self, session_id: str):
        """Update last activity timestamp for a session"""
        if session_id in self._states:
            self._states[session_id].last_activity = datetime.now()

    async def cleanup_stale_connections(self):
        """Remove connections that have timed out"""
        now = datetime.now()
        stale_sessions = []

        for session_id, state in self._states.items():
            elapsed = (now - state.last_activity).total_seconds()
            if elapsed > self.CONNECTION_TIMEOUT:
                stale_sessions.append(session_id)

        for session_id in stale_sessions:
            await self.disconnect(session_id)

    def get_active_connections_count(self) -> int:
        """Get number of active connections"""
        return len(self._connections)

    def get_session_state(self, session_id: str) -> Optional[ConnectionState]:
        """Get state for a session"""
        return self._states.get(session_id)


# Global manager instance
_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get or create the WebSocket manager singleton"""
    global _manager
    if _manager is None:
        _manager = WebSocketManager()
    return _manager
