"""
Pydantic models for API requests/responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class MessageRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000)
    source: str = "unknown"
    metadata: Optional[Dict[str, Any]] = {}


class MessageResponse(BaseModel):
    session_id: str
    response: str
    state: str
    confidence: float
    brain_used: str
    processing_time_ms: float


class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    message_count: int
    current_state: str
    is_active: bool


class SystemStatus(BaseModel):
    status: str
    active_sessions: int
    total_conversations: int
    uptime_seconds: float
    version: str = "1.0.0"


class IntelligenceReport(BaseModel):
    conversation_id: str
    scam_type: str
    confidence: float
    extracted_iocs: List[Dict]
    tactics_identified: List[str]
    recommended_actions: List[str]
    generated_at: datetime