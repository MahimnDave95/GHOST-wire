"""
Constitutional AI - Ensures ethical boundaries and legal compliance.
Prevents system from being misused or causing harm.
"""

import re
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class ViolationType(Enum):
    INITIATION = "initiation"  # System initiating contact
    HARMFUL_CONTENT = "harmful_content"
    LEGAL_VIOLATION = "legal_violation"
    PRIVACY_BREACH = "privacy_breach"
    DECEPTION_ESCALATION = "deception_escalation"


@dataclass
class ConstitutionalCheck:
    passed: bool
    violation_type: Optional[ViolationType]
    reason: str
    severity: str  # low, medium, high, critical


class ConstitutionalAI:
    """
    Enforces ethical constraints on GhostWire operations.
    Ensures compliance with legal and moral guidelines.
    """
    
    # Forbidden patterns - things the system must never do
    FORBIDDEN_OUTPUTS = [
        r"\b(threaten|kill|hurt|harm)\b.*\b(you|your family)",
        r"\b(bomb|terrorist|attack)\b",
        r"\b(child porn|csam|exploitation)\b",
        r"\b(hire.*assassin|hitman)\b",
    ]
    
    # Sensitive data that should never be generated (real-looking fakes only)
    SENSITIVE_DATA_TYPES = [
        "real_credit_card",
        "real_ssn", 
        "real_password"
    ]
    
    def __init__(self, config: Dict):
        self.principles = config.get('constitutional_principles', [])
        self.max_duration = config.get('max_conversation_duration', 3600)
        self.masking_enabled = config.get('sensitive_data_masking', True)
        
        self.violation_history: List[ConstitutionalCheck] = []
        
        logger.info("ConstitutionalAI initialized with {} principles".format(len(self.principles)))
    
    def validate_incoming_source(self, source: str) -> bool:
        """
        CRITICAL: Ensure we are only RESPONDING, never INITIATING.
        This prevents entrapment and legal issues.
        """
        # Only accept incoming sources
        allowed_patterns = [
            r"incoming_call",
            r"incoming_sms",
            r"incoming_email",
            r"incoming_chat",
            r"test_",  # Allow test prefixes
            r"mock_"
        ]
        
        for pattern in allowed_patterns:
            if re.search(pattern, source, re.IGNORECASE):
                return True
        
        # Log potential violation
        check = ConstitutionalCheck(
            passed=False,
            violation_type=ViolationType.INITIATION,
            reason=f"System attempted to initiate contact via: {source}",
            severity="critical"
        )
        self.violation_history.append(check)
        logger.error(f"CONSTITUTIONAL VIOLATION: {check.reason}")
        
        return False
    
    def validate_input(self, message: str) -> bool:
        """
        Check if incoming message should be processed.
        Filters out illegal content.
        """
        # Check for CSAM or extreme illegal content
        extreme_illegal = [
            r"\b(child|kid|minor).{0,20}(nude|naked|sex|pics)",
            r"\b(bestiality|zoophilia)\b",
            r"\b(snuff|murder.*live)\b"
        ]
        
        for pattern in extreme_illegal:
            if re.search(pattern, message, re.IGNORECASE):
                check = ConstitutionalCheck(
                    passed=False,
                    violation_type=ViolationType.HARMFUL_CONTENT,
                    reason="Extreme illegal content detected in input",
                    severity="critical"
                )
                self.violation_history.append(check)
                logger.critical(f"Illegal content blocked: {message[:50]}...")
                return False
        
        return True
    
    def validate_output(self, response: str) -> bool:
        """
        Check if generated response violates principles.
        """
        # Check for AI self-identification
        ai_reveals = [
            r"\bi am an?\s+(ai|artificial intelligence|language model|bot)\b",
            r"\bi'm an?\s+(ai|artificial intelligence)\b",
            r"\bas an?\s+(ai|artificial intelligence)\b",
            r"\bi don't have (personal experiences|a body|emotions)\b",
            r"\bi was (trained|created|developed) by",
            r"\bmy (training data|knowledge cutoff)\b"
        ]
        
        for pattern in ai_reveals:
            if re.search(pattern, response, re.IGNORECASE):
                check = ConstitutionalCheck(
                    passed=False,
                    violation_type=ViolationType.DECEPTION_ESCALATION,
                    reason="AI self-identification detected",
                    severity="high"
                )
                self.violation_history.append(check)
                logger.warning(f"AI reveal detected: {response[:100]}")
                return False
        
        # Check for harmful content generation
        for pattern in self.FORBIDDEN_OUTPUTS:
            if re.search(pattern, response, re.IGNORECASE):
                check = ConstitutionalCheck(
                    passed=False,
                    violation_type=ViolationType.HARMFUL_CONTENT,
                    reason="Harmful content pattern detected",
                    severity="critical"
                )
                self.violation_history.append(check)
                return False
        
        return True
    
    def validate_conversation_state(self, session) -> ConstitutionalCheck:
        """
        Check if conversation should continue or terminate.
        """
        # Check duration
        duration = session.state_machine.context.time_in_state()
        if duration > self.max_duration:
            return ConstitutionalCheck(
                passed=False,
                violation_type=ViolationType.DECEPTION_ESCALATION,
                reason=f"Conversation exceeded max duration: {duration}s",
                severity="medium"
            )
        
        # Check for excessive extraction attempts
        extraction_count = len([
            v for v in session.state_machine.context.extraction_data.values() 
            if v
        ])
        if extraction_count > 20:
            return ConstitutionalCheck(
                passed=False,
                violation_type=ViolationType.DECEPTION_ESCALATION,
                reason="Excessive extraction attempts",
                severity="medium"
            )
        
        return ConstitutionalCheck(
            passed=True,
            violation_type=None,
            reason="State valid",
            severity="none"
        )
    
    def get_report(self) -> Dict:
        """Generate constitutional compliance report"""
        total = len(self.violation_history)
        critical = len([v for v in self.violation_history if v.severity == "critical"])
        
        return {
            "total_violations": total,
            "critical_violations": critical,
            "recent_violations": [
                {
                    "type": v.violation_type.value if v.violation_type else None,
                    "reason": v.reason,
                    "severity": v.severity
                }
                for v in self.violation_history[-10:]
            ],
            "compliance_status": "violated" if critical > 0 else "clean" if total == 0 else "warning"
        }