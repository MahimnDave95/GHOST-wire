"""
FastAPI routes for GhostWire API.
"""

import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import time
from typing import Optional

from .models import (
    MessageRequest, MessageResponse, SessionInfo, 
    SystemStatus, IntelligenceReport
)


router = APIRouter()

# Global engine reference (set in main.py)
engine = None


def get_engine():
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    return engine


@router.post("/chat", response_model=MessageResponse)
async def chat(
    request: MessageRequest,
    background_tasks: BackgroundTasks
):
    """
    Main chat endpoint. Creates or continues conversation.
    """
    start_time = time.time()
    
    try:
        # Get or create session
        if request.session_id and request.session_id in engine.sessions:
            session = engine.sessions[request.session_id]
        else:
            session = await engine.create_session(request.source)
        
        # Process message
        response_text = await engine.get_response(
            session.session_id, 
            request.message
        )
        
        if response_text is None:
            raise HTTPException(status_code=400, detail="Message rejected by security filter")
        
        processing_time = (time.time() - start_time) * 1000
        
        return MessageResponse(
            session_id=session.session_id,
            response=response_text,
            state=session.state_machine.get_current_state().value,
            confidence=0.8,  # Would come from actual brain
            brain_used="cortex",  # Would be dynamic
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in engine.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = engine.sessions[session_id]
    return SessionInfo(
        session_id=session_id,
        created_at=session.created_at,
        message_count=session.message_count,
        current_state=session.state_machine.get_current_state().value,
        is_active=not session.state_machine.is_terminal()
    )


@router.post("/session/{session_id}/end")
async def end_session(session_id: str):
    """Force end a conversation"""
    if session_id not in engine.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = engine.sessions[session_id]
    session.state_machine.force_termination("API request")
    
    return {"status": "terminated", "session_id": session_id}


@router.get("/status", response_model=SystemStatus)
async def get_status():
    """Get system status"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    return SystemStatus(
        status="operational",
        active_sessions=len(engine.sessions),
        total_conversations=engine.memory.get_statistics().get("total", 0),
        uptime_seconds=time.time() - process.create_time()
    )


@router.get("/report/{session_id}", response_model=IntelligenceReport)
async def get_report(session_id: str):
    """Get intelligence report for conversation"""
    if session_id not in engine.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = engine.sessions[session_id]
    
    # Generate report from extraction data
    extraction_data = session.state_machine.context.extraction_data
    
    return IntelligenceReport(
        conversation_id=session_id,
        scam_type=extraction_data.get("scam_type", "unknown"),
        confidence=extraction_data.get("confidence", 0.0),
        extracted_iocs=extraction_data.get("iocs", []),
        tactics_identified=extraction_data.get("tactics", []),
        recommended_actions=["Report to authorities", "Block number"],
        generated_at=datetime.now()
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "llm_available": await engine.router.llm.check_ollama(),
        "database_connected": True  # Would check actual connection
    }