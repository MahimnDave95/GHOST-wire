"""
Finite State Machine for conversation flow management.
Handles transitions between scam detection phases.
"""

from enum import Enum, auto
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
from loguru import logger


class State(Enum):
    IDLE = "idle"
    INITIAL_CONTACT = "initial_contact"
    TRUST_BUILDING = "trust_building"
    SUSPICION_AROUSAL = "suspicion_arousal"
    EXTRACTION = "extraction"
    TERMINATION = "termination"


@dataclass
class StateContext:
    """Context maintained across state transitions"""
    conversation_id: str
    current_state: State = State.IDLE
    previous_states: List[State] = field(default_factory=list)
    state_entry_time: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    extraction_data: Dict = field(default_factory=dict)
    
    def transition_to(self, new_state: State) -> None:
        """Record state transition"""
        self.previous_states.append(self.current_state)
        self.current_state = new_state
        self.state_entry_time = datetime.now()
        
    def time_in_state(self) -> float:
        """Seconds spent in current state"""
        return (datetime.now() - self.state_entry_time).total_seconds()


class ConversationStateMachine:
    """
    Manages conversation lifecycle with scammer.
    Ensures natural flow while maximizing intelligence extraction.
    """
    
    # Valid state transitions
    TRANSITIONS = {
        State.IDLE: [State.INITIAL_CONTACT],
        State.INITIAL_CONTACT: [State.TRUST_BUILDING, State.SUSPICION_AROUSAL, State.TERMINATION],
        State.TRUST_BUILDING: [State.SUSPICION_AROUSAL, State.EXTRACTION, State.TERMINATION],
        State.SUSPICION_AROUSAL: [State.TRUST_BUILDING, State.EXTRACTION, State.TERMINATION],
        State.EXTRACTION: [State.EXTRACTION, State.TERMINATION],
        State.TERMINATION: []
    }
    
    def __init__(self, conversation_id: str, max_transitions: int = 20):
        self.context = StateContext(conversation_id=conversation_id)
        self.max_transitions = max_transitions
        self.transition_count = 0
        self._state_handlers: Dict[State, Callable] = {}
        self._entry_hooks: Dict[State, List[Callable]] = {}
        self._exit_hooks: Dict[State, List[Callable]] = {}
        
        logger.info(f"StateMachine initialized for conversation {conversation_id}")
    
    def register_handler(self, state: State, handler: Callable) -> None:
        """Register handler for state processing"""
        self._state_handlers[state] = handler
    
    def register_hook(self, hook_type: str, state: State, callback: Callable) -> None:
        """Register entry/exit hooks"""
        if hook_type == "entry":
            self._entry_hooks.setdefault(state, []).append(callback)
        elif hook_type == "exit":
            self._exit_hooks.setdefault(state, []).append(callback)
    
    def can_transition(self, target_state: State) -> bool:
        """Check if transition is valid"""
        if self.transition_count >= self.max_transitions:
            logger.warning("Max transitions reached, forcing termination")
            return target_state == State.TERMINATION
            
        return target_state in self.TRANSITIONS.get(self.context.current_state, [])
    
    def transition(self, target_state: State, reason: str = "") -> bool:
        """
        Attempt state transition with validation.
        Returns success status.
        """
        if not self.can_transition(target_state):
            logger.error(
                f"Invalid transition: {self.context.current_state.value} -> {target_state.value}"
            )
            return False
        
        # Execute exit hooks
        for hook in self._exit_hooks.get(self.context.current_state, []):
            try:
                hook(self.context)
            except Exception as e:
                logger.error(f"Exit hook error: {e}")
        
        old_state = self.context.current_state
        self.context.transition_to(target_state)
        self.transition_count += 1
        
        # Execute entry hooks
        for hook in self._entry_hooks.get(target_state, []):
            try:
                hook(self.context)
            except Exception as e:
                logger.error(f"Entry hook error: {e}")
        
        logger.info(
            f"State transition: {old_state.value} -> {target_state.value} "
            f"(Reason: {reason}) [Transition #{self.transition_count}]"
        )
        return True
    
    def get_current_state(self) -> State:
        return self.context.current_state
    
    def should_extract(self) -> bool:
        """Determine if we're in extraction-ready state"""
        return self.context.current_state in [
            State.SUSPICION_AROUSAL, 
            State.EXTRACTION
        ]
    
    def is_terminal(self) -> bool:
        return self.context.current_state == State.TERMINATION
    
    def force_termination(self, reason: str) -> None:
        """Force conversation end"""
        if not self.is_terminal():
            self.transition(State.TERMINATION, f"FORCED: {reason}")
    
    def to_dict(self) -> Dict:
        """Serialize state for persistence"""
        return {
            "conversation_id": self.context.conversation_id,
            "current_state": self.context.current_state.value,
            "previous_states": [s.value for s in self.context.previous_states],
            "transition_count": self.transition_count,
            "time_in_current_state": self.context.time_in_state(),
            "metadata": self.context.metadata,
            "extraction_data": self.context.extraction_data
        }
    
    def __repr__(self) -> str:
        return f"<StateMachine {self.context.conversation_id}: {self.context.current_state.value}>"