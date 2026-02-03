"""
Brain Router - Decides which brain (Reflex or Cortex) handles each interaction.
Balances speed vs sophistication based on conversation context.
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
import asyncio
from loguru import logger

from .reflex_brain import ReflexBrain
from .cortex_brain import CortexBrain


@dataclass
class RoutingDecision:
    brain: str  # 'reflex' or 'cortex'
    confidence: float
    reason: str
    latency_budget_ms: int


class BrainRouter:
    """
    Intelligent routing between fast reflexes and slow reasoning.
    Optimizes for both engagement quality and intelligence extraction.
    """
    
    def __init__(self, llm_config: Dict):
        self.reflex = ReflexBrain()
        self.cortex = CortexBrain(llm_config)
        
        # Routing thresholds
        self.urgency_threshold = 0.7  # Use cortex if urgency > this
        self.complexity_threshold = 50  # Words
        
        logger.info("BrainRouter initialized")
    
    async def route(
        self,
        message: str,
        session,
        persona
    ) -> str:
        """
        Route message to appropriate brain and return response.
        """
        # Get routing decision
        decision = self._decide_brain(message, session)
        
        persona_prompt = persona.generate_system_prompt() if persona.get_active_persona() else ""
        state_context = session.state_machine.context.to_dict()
        
        # Extract intelligence goals based on state
        extraction_goals = self._get_extraction_goals(session)
        
        if decision.brain == "reflex":
            # Fast path
            matches = self.reflex.analyze(message)
            response, metadata = self.reflex.generate_response(
                matches,
                {
                    "age": persona.get_active_persona().age if persona.get_active_persona() else 70,
                    "name": persona.get_active_persona().name if persona.get_active_persona() else "User"
                }
            )
            
            if metadata.get("used"):
                # Check if we should escalate to cortex
                if metadata.get("confidence", 0) > 0.8:
                    # High-confidence scam detected, use cortex for better extraction
                    decision = RoutingDecision(
                        brain="cortex",
                        confidence=0.9,
                        reason="High-confidence scam, escalating for extraction",
                        latency_budget_ms=5000
                    )
                else:
                    # Log reflex response
                    await self._log_response(session, response, metadata)
                    return response
        
        # Cortex path (or fallback)
        if decision.brain == "cortex":
            response, metadata = await self.cortex.generate_response(
                message=message,
                session_id=session.session_id,
                persona_system_prompt=persona_prompt,
                state_context=state_context,
                extraction_goals=extraction_goals
            )
            
            await self._log_response(session, response, metadata)
            return response
        
        # Should never reach here
        return "I'm not sure how to respond to that."
    
    def _decide_brain(self, message: str, session) -> RoutingDecision:
        """
        Decide which brain to use based on message and session state.
        """
        urgency = self.reflex.get_urgency_score(message)
        word_count = len(message.split())
        state = session.state_machine.get_current_state()
        
        # Always use cortex for extraction phase
        if state.value in ["extraction", "suspicion_arousal"]:
            return RoutingDecision(
                brain="cortex",
                confidence=0.9,
                reason="Active extraction phase",
                latency_budget_ms=5000
            )
        
        # Use cortex for high urgency
        if urgency > self.urgency_threshold:
            return RoutingDecision(
                brain="cortex",
                confidence=urgency,
                reason=f"High urgency score: {urgency:.2f}",
                latency_budget_ms=4000
            )
        
        # Use cortex for complex messages
        if word_count > self.complexity_threshold:
            return RoutingDecision(
                brain="cortex",
                confidence=0.6,
                reason=f"Complex message: {word_count} words",
                latency_budget_ms=4000
            )
        
        # Default to reflex for speed
        return RoutingDecision(
            brain="reflex",
            confidence=0.8,
            reason="Low complexity, using fast path",
            latency_budget_ms=100
        )
    
    def _get_extraction_goals(self, session) -> list:
        """Determine what intelligence to extract based on conversation state"""
        state = session.state_machine.get_current_state()
        
        goals = {
            "initial_contact": [
                "Identify scam type",
                "Determine if human or bot",
                "Extract origin/organization name"
            ],
            "trust_building": [
                "Get callback number",
                "Identify payment methods accepted",
                "Understand their script/flow"
            ],
            "suspicion_arousal": [
                "Extract specific financial details requested",
                "Get account/wallet information",
                "Identify accomplices or upstream contacts"
            ],
            "extraction": [
                "Confirm payment receiving details",
                "Document all IOCs",
                "Map complete operation structure"
            ]
        }
        
        return goals.get(state.value, ["Maintain engagement"])
    
    async def _log_response(self, session, response: str, metadata: Dict) -> None:
        """Log response metadata"""
        # Update state machine based on response
        if metadata.get("brain") == "reflex":
            if metadata.get("category") == "financial":
                session.state_machine.transition(
                    session.state_machine.get_current_state(),  # Stay or move
                    f"Detected {metadata.get('pattern')}"
                )
        
        logger.debug(f"Response generated: brain={metadata.get('brain')}, confidence={metadata.get('confidence')}")