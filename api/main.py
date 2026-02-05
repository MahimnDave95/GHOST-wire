# """
# GhostWire API Entry Point.
# FastAPI application with lifespan management.
# """

# import asyncio
# from contextlib import asynccontextmanager
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn
# from loguru import logger

# # Import engine and routes
# from core.engine import GhostWireEngine
# from api import routes


# # Global engine instance
# engine: GhostWireEngine = None


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Manage application lifespan"""
#     global engine
    
#     # Startup
#     logger.info("Starting GhostWire...")
#     engine = GhostWireEngine()
    
#     # Set active persona
#     engine.persona_manager.set_active_persona("elderly_coimbatore")
    
#     # Inject engine into routes
#     routes.engine = engine
    
#     # Start cleanup task
#     cleanup_task = asyncio.create_task(periodic_cleanup())
    
#     logger.info("GhostWire started successfully")
    
#     yield
    
#     # Shutdown
#     logger.info("Shutting down GhostWire...")
#     cleanup_task.cancel()
#     engine.shutdown()


# async def periodic_cleanup():
#     """Periodic maintenance tasks"""
#     while True:
#         try:
#             await asyncio.sleep(300)  # Every 5 minutes
#             cleaned = await engine.cleanup_old_sessions()
#             if cleaned > 0:
#                 logger.info(f"Cleaned up {cleaned} old sessions")
#         except asyncio.CancelledError:
#             break
#         except Exception as e:
#             logger.error(f"Cleanup error: {e}")


# # Create FastAPI app
# app = FastAPI(
#     title="GhostWire API",
#     description="Agentic Honey-Pot for Scam Detection",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Restrict in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(routes.router, prefix="/api/v1")


# @app.get("/")
# async def root():
#     return {
#         "name": "GhostWire",
#         "version": "1.0.0",
#         "status": "operational",
#         "docs": "/docs"
#     }


# if __name__ == "__main__":
#     uvicorn.run(
#         "api.main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=False,
#         log_level="info"
#     )
"""
GhostWire Hackathon API - Public Endpoint Version
Problem 2: Agentic Honey-Pot for Scam Detection
"""

import os
import asyncio
import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uvicorn
from loguru import logger

# API Key from environment
API_KEY = os.getenv("GHOSTWIRE_API_KEY", "gw-hackathon-2024-secure-key")

# Request/Response Models
class ExtractRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="Scammer message to analyze")
    session_id: Optional[str] = Field(default=None, description="Optional session ID for continuity")
    source: str = Field(default="unknown", description="Source of message (sms, email, call, chat)")

class IOC(BaseModel):
    type: str
    value: str
    confidence: float

class ExtractedIntelligence(BaseModel):
    iocs: List[IOC]
    scam_category: str
    confidence_score: float
    tactics_detected: List[str]
    recommended_action: str

class ExtractResponse(BaseModel):
    status: str
    session_id: str
    extracted_intelligence: ExtractedIntelligence
    persona_response: str
    processing_time_ms: float

class HealthResponse(BaseModel):
    status: str
    version: str
    problem_statement: str

# FastAPI App
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("GhostWire Hackathon API starting...")
    yield
    logger.info("GhostWire Hackathon API shutting down...")

app = FastAPI(
    title="GhostWire - Agentic Honey-Pot API",
    description="Problem 2: Extracts intelligence from scam messages using AI personas",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key verification
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# In-memory storage for hackathon (use Redis/DB in production)
sessions: Dict[str, Dict] = {}

# Import extraction engine (simplified for hackathon)
from extraction.patterns import ExtractionEngine
from extraction.tactics import TacticClassifier

extraction_engine = ExtractionEngine()
tactic_classifier = TacticClassifier()

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="operational",
        version="1.0.0",
        problem_statement="Problem 2: Agentic Honey-Pot for Scam Detection"
    )

@app.post("/api/v1/extract", response_model=ExtractResponse)
async def extract_intelligence(
    request: ExtractRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Main endpoint for hackathon evaluation.
    Accepts scam message, returns extracted intelligence.
    """
    start_time = time.time()
    
    try:
        # Generate or use provided session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize session if new
        if session_id not in sessions:
            sessions[session_id] = {
                "created_at": datetime.utcnow(),
                "message_count": 0,
                "extracted_iocs": []
            }
        
        sessions[session_id]["message_count"] += 1
        
        # Extract IOCs
        iocs = extraction_engine._extract_iocs(
            text=request.message,
            context=f"Hackathon evaluation: {request.source}",
            conversation_id=session_id
        )
        
        # Classify tactics
        tactic_profile = tactic_classifier.classify(request.message)
        
        # Generate persona response (simplified)
        persona_response = generate_persona_response(
            request.message, 
            tactic_profile.primary_category.value
        )
        
        # Build response
        processing_time = (time.time() - start_time) * 1000
        
        response = ExtractResponse(
            status="success",
            session_id=session_id,
            extracted_intelligence=ExtractedIntelligence(
                iocs=[
                    IOC(type=ioc.ioc_type, value=ioc.value, confidence=ioc.confidence)
                    for ioc in iocs[:10]  # Limit to top 10
                ],
                scam_category=tactic_profile.primary_category.value,
                confidence_score=tactic_profile.confidence,
                tactics_detected=[t.tactic for t in tactic_classifier.classify(request.message).__dict__.get('key_indicators', [])] or ["social_engineering"],
                recommended_action="block_and_report" if tactic_profile.confidence > 0.7 else "monitor"
            ),
            persona_response=persona_response,
            processing_time_ms=round(processing_time, 2)
        )
        
        # Store for session continuity
        sessions[session_id]["last_extracted"] = response.extracted_intelligence.dict()
        
        logger.info(f"Extracted {len(iocs)} IOCs for session {session_id}")
        return response
        
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_persona_response(message: str, scam_category: str) -> str:
    """Generate contextual persona response based on scam type"""
    responses = {
        "tech_support": [
            "Oh my! I don't understand computers. My son handles this.",
            "What is AnyDesk? I only know how to open Facebook.",
            "My computer is very old, it makes funny noises sometimes."
        ],
        "lottery_scam": [
            "I never win anything! Are you sure you have right number?",
            "My husband always said I was lucky, but I don't trust this.",
            "Do I need to pay money to get prize? I don't have much."
        ],
        "phishing": [
            "I don't like giving my bank details on phone.",
            "Can I call you back on official number?",
            "My children told me to be careful about these calls."
        ],
        "romance_scam": [
            "You are very kind. I don't get many compliments.",
            "I miss my husband, he passed away 5 years ago.",
            "Where are you from? You sound nice."
        ],
        "investment_scam": [
            "My son handles all investments. I only have pension.",
            "Guaranteed returns? My bank doesn't give that.",
            "I don't understand bitcoin, is it like share market?"
        ],
        "extortion": [
            "Police? But I am good person, I never did anything!",
            "My son is lawyer, should I call him?",
            "Please don't arrest me, I am old woman."
        ]
    }
    
    import random
    category_responses = responses.get(scam_category, responses["phishing"])
    return random.choice(category_responses)

@app.get("/api/v1/session/{session_id}")
async def get_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get session history"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.post("/api/v1/session/{session_id}/end")
async def end_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """End session and generate final report"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = sessions.pop(session_id)
    return {
        "status": "terminated",
        "session_id": session_id,
        "summary": session_data
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)