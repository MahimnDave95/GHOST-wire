"""
GhostWire API Entry Point.
FastAPI application with lifespan management.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger

# Import engine and routes
from core.engine import GhostWireEngine
from api import routes


# Global engine instance
engine: GhostWireEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global engine
    
    # Startup
    logger.info("Starting GhostWire...")
    engine = GhostWireEngine()
    
    # Set active persona
    engine.persona_manager.set_active_persona("elderly_coimbatore")
    
    # Inject engine into routes
    routes.engine = engine
    
    # Start cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    logger.info("GhostWire started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GhostWire...")
    cleanup_task.cancel()
    engine.shutdown()


async def periodic_cleanup():
    """Periodic maintenance tasks"""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            cleaned = await engine.cleanup_old_sessions()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} old sessions")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# Create FastAPI app
app = FastAPI(
    title="GhostWire API",
    description="Agentic Honey-Pot for Scam Detection",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "GhostWire",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )