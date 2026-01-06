"""Feedback API routes"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    """Feedback submission request"""

    message_id: str = Field(..., description="ID of the message being rated")
    session_id: Optional[str] = Field(None, description="Session ID")
    feedback_type: str = Field(
        ..., description="Type of feedback: 'positive' or 'negative'"
    )
    categories: Optional[List[str]] = Field(
        None, description="Categories for negative feedback"
    )
    comment: Optional[str] = Field(None, max_length=500, description="Additional comment")


class FeedbackResponse(BaseModel):
    """Feedback submission response"""

    success: bool
    feedback_id: str
    message: str


class FeedbackStats(BaseModel):
    """Feedback statistics"""

    total_feedback: int
    positive_count: int
    negative_count: int
    positive_rate: float
    top_categories: List[dict]


# In-memory storage (replace with database in production)
_feedback_storage: List[dict] = []

# File-based storage path
FEEDBACK_FILE = Path("./data/feedback.json")


def _load_feedback():
    """Load feedback from file"""
    global _feedback_storage
    if FEEDBACK_FILE.exists():
        try:
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                _feedback_storage = json.load(f)
        except (json.JSONDecodeError, IOError):
            _feedback_storage = []


def _save_feedback():
    """Save feedback to file"""
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(_feedback_storage, f, ensure_ascii=False, indent=2)


def _generate_feedback_id() -> str:
    """Generate unique feedback ID"""
    import uuid

    return f"fb_{uuid.uuid4().hex[:12]}"


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit user feedback for a message.

    - **message_id**: ID of the message being rated
    - **feedback_type**: 'positive' (thumbs up) or 'negative' (thumbs down)
    - **categories**: Optional categories for negative feedback
    - **comment**: Optional additional comment
    """
    if request.feedback_type not in ("positive", "negative"):
        raise HTTPException(
            status_code=400,
            detail="feedback_type must be 'positive' or 'negative'",
        )

    feedback_id = _generate_feedback_id()

    feedback_entry = {
        "feedback_id": feedback_id,
        "message_id": request.message_id,
        "session_id": request.session_id,
        "feedback_type": request.feedback_type,
        "categories": request.categories or [],
        "comment": request.comment,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    _feedback_storage.append(feedback_entry)

    # Save to file in background
    background_tasks.add_task(_save_feedback)

    return FeedbackResponse(
        success=True,
        feedback_id=feedback_id,
        message="피드백이 성공적으로 저장되었습니다.",
    )


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats():
    """
    Get feedback statistics.

    Returns aggregated statistics about user feedback.
    """
    if not _feedback_storage:
        return FeedbackStats(
            total_feedback=0,
            positive_count=0,
            negative_count=0,
            positive_rate=0.0,
            top_categories=[],
        )

    total = len(_feedback_storage)
    positive = sum(1 for f in _feedback_storage if f["feedback_type"] == "positive")
    negative = total - positive

    # Count categories
    category_counts = {}
    for feedback in _feedback_storage:
        for category in feedback.get("categories", []):
            category_counts[category] = category_counts.get(category, 0) + 1

    # Sort by count
    top_categories = [
        {"category": cat, "count": count}
        for cat, count in sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]
    ]

    return FeedbackStats(
        total_feedback=total,
        positive_count=positive,
        negative_count=negative,
        positive_rate=positive / total if total > 0 else 0.0,
        top_categories=top_categories,
    )


@router.get("/recent")
async def get_recent_feedback(limit: int = 10):
    """
    Get recent feedback entries.

    - **limit**: Maximum number of entries to return (default: 10)
    """
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100",
        )

    # Sort by timestamp descending
    sorted_feedback = sorted(
        _feedback_storage,
        key=lambda x: x.get("timestamp", ""),
        reverse=True,
    )

    return {
        "feedback": sorted_feedback[:limit],
        "total": len(_feedback_storage),
    }


@router.delete("/clear")
async def clear_feedback(confirm: bool = False):
    """
    Clear all feedback data.

    - **confirm**: Must be True to confirm deletion
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Set confirm=true to delete all feedback",
        )

    global _feedback_storage
    _feedback_storage = []

    if FEEDBACK_FILE.exists():
        FEEDBACK_FILE.unlink()

    return {"success": True, "message": "모든 피드백이 삭제되었습니다."}


# Load existing feedback on module import
_load_feedback()
