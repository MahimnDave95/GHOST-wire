"""
GhostWire Core Module

This module contains the fundamental components of the GhostWire honey-pot system:
- Engine: Main orchestration and session management
- State Machine: Conversation flow control
- Persona Manager: Decoy identity management
- Memory Manager: Persistent storage and retrieval
"""

from .engine import GhostWireEngine, ConversationSession
from .state_machine import ConversationStateMachine, State, StateContext
from .persona_manager import PersonaManager, PersonaProfile
from .memory_manager import MemoryManager, MemoryEntry

__version__ = "1.0.0"
__author__ = "GhostWire Project"

__all__ = [
    # Main Engine
    "GhostWireEngine",
    "ConversationSession",
    
    # State Management
    "ConversationStateMachine",
    "State",
    "StateContext",
    
    # Persona Management
    "PersonaManager",
    "PersonaProfile",
    
    # Memory Management
    "MemoryManager",
    "MemoryEntry",
]

# Module level logger
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())