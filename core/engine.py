"""
Main GhostWire Engine - Orchestrates conversation flow between
scammer detection, persona management, and intelligence extraction.
"""

import asyncio
import uuid
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from loguru import logger

from .state_machine import ConversationStateMachine, State
from .persona_manager import PersonaManager
from .memory_manager import MemoryManager, MemoryEntry


class ConversationSession:
    """Individual conversation handler"""
    
    def __init__(
        self,
        session_id: str,
        engine: 'GhostWireEngine',
        source: str = "unknown"
    ):
        self.session_id = session_id
        self.engine = engine
        self.source = source
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.message_count = 0
        
        # Initialize components
        self.state_machine = ConversationStateMachine(session_id)
        self._setup_state_handlers()
        
        logger.info(f"New session created: {session_id} from {source}")
    
    def _setup_state_handlers(self) -> None:
        """Configure state-specific behaviors"""
        # Register state entry hooks
        self.state_machine.register_hook(
            "entry", State.EXTRACTION, 
            lambda ctx: logger.info(f"Entering extraction phase: {ctx.conversation_id}")
        )
        
        self.state_machine.register_hook(
            "entry", State.TERMINATION,
            self._on_termination
        )
    
    def _on_termination(self, context) -> None:
        """Cleanup on conversation end"""
        logger.info(f"Conversation terminating: {context.conversation_id}")
        # Trigger final extraction report generation
        asyncio.create_task(self._generate_final_report())
    
    async def _generate_final_report(self) -> None:
        """Generate intelligence report from conversation"""
        # Implementation would compile extraction data
        pass
    
    async def process_message(self, message: str) -> str:
        """
        Main entry point for incoming messages.
        Routes through appropriate brain and extracts intelligence.
        """
        self.last_activity = datetime.now()
        self.message_count += 1
        
        # Store incoming message
        self.engine.memory.store(MemoryEntry(
            conversation_id=self.session_id,
            memory_type="short_term",
            content=f"SCAMMER: {message}",
            importance=0.6
        ))
        
        # Route to appropriate brain
        response = await self.engine.router.route(
            message=message,
            session=self,
            persona=self.engine.persona_manager
        )
        
        # Validate persona consistency
        is_valid, violations = self.engine.persona_manager.validate_response(response)
        if not is_valid:
            logger.warning(f"Persona violations in response: {violations}")
            # Could regenerate response or flag for review
        
        # Store outgoing response
        self.engine.memory.store(MemoryEntry(
            conversation_id=self.session_id,
            memory_type="short_term", 
            content=f"PERSONA: {response}",
            importance=0.6
        ))
        
        # Extract intelligence if in appropriate state
        if self.state_machine.should_extract():
            await self._extract_intelligence(message, response)
        
        # Check for conversation termination conditions
        await self._check_termination_conditions()
        
        return response
    
    async def _extract_intelligence(self, incoming: str, outgoing: str) -> None:
        """Extract IOCs and tactics from conversation"""
        extraction_data = await self.engine.extraction_engine.extract(
            incoming, outgoing, self.session_id
        )
        
        if extraction_data:
            # Store encrypted extraction
            self.engine.memory.store(MemoryEntry(
                conversation_id=self.session_id,
                memory_type="extracted_ioc",
                content=json.dumps(extraction_data),
                importance=0.9
            ), encrypt=True)
            
            # Update state machine context
            self.state_machine.context.extraction_data.update(extraction_data)
    
    async def _check_termination_conditions(self) -> None:
        """Check if conversation should end"""
        # Max messages
        if self.message_count > 100:
            self.state_machine.force_termination("Max messages reached")
            return
        
        # Max duration
        duration = (datetime.now() - self.created_at).total_seconds()
        if duration > 3600:  # 1 hour
            self.state_machine.force_termination("Max duration reached")
            return
        
        # Inactivity
        # (Would be checked by external scheduler)
    
    def get_status(self) -> Dict[str, Any]:
        """Get session status"""
        return {
            "session_id": self.session_id,
            "state": self.state_machine.get_current_state().value,
            "message_count": self.message_count,
            "duration_seconds": (datetime.now() - self.created_at).total_seconds(),
            "source": self.source
        }


class GhostWireEngine:
    """
    Main orchestrator for the GhostWire honey-pot system.
    Manages sessions, coordinates components, ensures ethical compliance.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.sessions: Dict[str, ConversationSession] = {}
        
        # Initialize components
        self.persona_manager = PersonaManager()
        self.memory = MemoryManager(
            db_path=self.config.get('storage', {}).get('database_url', 'sqlite:///data/ghostwire.db').replace('sqlite:///', '')
        )
        
        # Brains (initialized lazily to avoid import cycles)
        self._router = None
        self._extraction_engine = None
        
        # Security
        from security.constitutional_ai import ConstitutionalAI
        from security.audit_logger import AuditLogger
        
        self.constitutional_ai = ConstitutionalAI(self.config.get('security', {}))
        self.audit_logger = AuditLogger(self.config.get('security', {}).get('audit', {}))
        
        logger.info("GhostWire Engine initialized")
    
    def _load_config(self, path: str) -> Dict:
        """Load YAML configuration"""
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    @property
    def router(self):
        """Lazy initialization of brain router"""
        if self._router is None:
            from brains.router import BrainRouter
            self._router = BrainRouter(self.config.get('llm', {}))
        return self._router
    
    @property
    def extraction_engine(self):
        """Lazy initialization of extraction engine"""
        if self._extraction_engine is None:
            from extraction.patterns import ExtractionEngine
            self._extraction_engine = ExtractionEngine()
        return self._extraction_engine
    
    async def create_session(self, source: str = "unknown") -> ConversationSession:
        """Create new conversation session"""
        session_id = str(uuid.uuid4())
        
        # Constitutional check - ensure we're not initiating
        if not self.constitutional_ai.validate_incoming_source(source):
            raise ValueError("Source failed constitutional validation")
        
        session = ConversationSession(session_id, self, source)
        self.sessions[session_id] = session
        
        # Audit log
        self.audit_logger.log_event("session_created", {
            "session_id": session_id,
            "source": source,
            "persona": self.persona_manager.get_active_persona().id if self.persona_manager.get_active_persona() else None
        })
        
        return session
    
    async def get_response(self, session_id: str, message: str) -> Optional[str]:
        """Get response for message in session"""
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            return None
        
        session = self.sessions[session_id]
        
        # Pre-processing security check
        if not self.constitutional_ai.validate_input(message):
            logger.warning(f"Input failed constitutional check: {message[:50]}...")
            return None
        
        try:
            response = await session.process_message(message)
            
            # Post-processing check
            if not self.constitutional_ai.validate_output(response):
                logger.warning("Output failed constitutional check, regenerating...")
                response = "I'm not sure I understand. Could you explain that differently?"
            
            self.audit_logger.log_event("message_exchanged", {
                "session_id": session_id,
                "input_length": len(message),
                "output_length": len(response)
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.audit_logger.log_event("error", {
                "session_id": session_id,
                "error": str(e)
            })
            return "Sorry, I'm having trouble understanding. My connection is bad."
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for all sessions"""
        return {
            "active_sessions": len(self.sessions),
            "sessions": [s.get_status() for s in self.sessions.values()]
        }
    
    async def cleanup_old_sessions(self, max_age_seconds: int = 7200) -> int:
        """Remove old inactive sessions"""
        now = datetime.now()
        to_remove = []
        
        for sid, session in self.sessions.items():
            age = (now - session.last_activity).total_seconds()
            if age > max_age_seconds or session.state_machine.is_terminal():
                to_remove.append(sid)
        
        for sid in to_remove:
            del self.sessions[sid]
        
        return len(to_remove)
    
    def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info("Shutting down GhostWire Engine...")
        self.memory.close()
        self.audit_logger.close()