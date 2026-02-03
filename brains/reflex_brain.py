"""
Reflex Brain - Fast pattern matching for immediate threat detection.
No LLM calls, just regex and keyword matching for speed.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class PatternMatch:
    pattern_name: str
    confidence: float
    matched_text: str
    category: str
    suggested_action: str


class ReflexBrain:
    """
    Ultra-fast pattern matching for common scam indicators.
    Runs locally with zero latency.
    """
    
    # Scam pattern database
    PATTERNS = {
        # Urgent pressure tactics
        "urgent_action": {
            "regex": r"\b(urgent|immediate|act now|limited time|expires?|deadline|hurry|asap|emergency)\b",
            "weight": 0.7,
            "category": "pressure_tactic"
        },
        "threat_legal": {
            "regex": r"\b(lawsuit|arrest|warrant|police|legal action|court|attorney|prosecuted|federal|crime)\b",
            "weight": 0.8,
            "category": "threat"
        },
        "threat_financial": {
            "regex": r"\b(account suspended|frozen|blocked|closure|terminate service|cancelled|overdue)\b",
            "weight": 0.75,
            "category": "threat"
        },
        
        # Financial extraction patterns
        "request_payment": {
            "regex": r"\b(pay|payment|send money|transfer|wire|deposit|fee|fine|penalty|dues)\b",
            "weight": 0.6,
            "category": "financial"
        },
        "request_giftcard": {
            "regex": r"\b(gift card|itunes|amazon card|google play|steam card|vanilla|reloadit)\b",
            "weight": 0.9,
            "category": "financial"
        },
        "request_crypto": {
            "regex": r"\b(bitcoin|btc|crypto|wallet|blockchain|ethereum|eth|usdt|tether)\b",
            "weight": 0.85,
            "category": "financial"
        },
        "request_bank_info": {
            "regex": r"\b(account number|routing|iban|swift|credit card|cvv|pin|password|login|ssn|social security)\b",
            "weight": 0.95,
            "category": "financial"
        },
        
        # Access requests
        "remote_access": {
            "regex": r"\b(anydesk|teamviewer|logmein|remote access|screen share|connect|take control)\b",
            "weight": 0.9,
            "category": "technical"
        },
        "software_install": {
            "regex": r"\b(download|install|click link|visit|go to|open|run|execute|setup)\b",
            "weight": 0.6,
            "category": "technical"
        },
        
        # Identity verification (phishing)
        "verify_identity": {
            "regex": r"\b(verify|confirm|validate|update your info|security check|authentication|kyc)\b",
            "weight": 0.5,
            "category": "phishing"
        },
        
        # Prize/lottery scams
        "prize_win": {
            "regex": r"\b(won|winner|prize|lottery|jackpot|inheritance|million|reward|lucky|selected|random)\b",
            "weight": 0.8,
            "category": "lottery"
        },
        
        # Romance/relationship
        "romance_signal": {
            "regex": r"\b(love|dear|honey|baby|sweetheart|beautiful|gorgeous|soulmate|destiny|god sent)\b",
            "weight": 0.4,
            "category": "romance"
        },
        
        # Tech support
        "tech_support_claim": {
            "regex": r"\b(microsoft|apple|amazon|netflix|irs|social security|tech support|help desk|service center)\b",
            "weight": 0.6,
            "category": "impersonation"
        },
        "virus_warning": {
            "regex": r"\b(virus|malware|hacked|infected|security breach|unauthorized|suspicious activity)\b",
            "weight": 0.7,
            "category": "technical"
        }
    }
    
    # Response templates based on category
    RESPONSES = {
        "pressure_tactic": [
            "Oh my, that sounds serious. I'm not very good with computers though, can you explain slowly?",
            "I'm a bit confused. My grandson usually helps me with these things.",
            "That sounds scary. Let me write this down. Can you repeat that?"
        ],
        "threat": [
            "I don't understand, I've always paid my bills on time. There must be a mistake?",
            "My son is a lawyer, should I call him about this?",
            "This is very worrying. I'm an old person, I don't want any trouble."
        ],
        "financial": [
            "I don't have much money, just my pension. How much are we talking about?",
            "I usually pay cash for everything. I don't trust these online things.",
            "My bank is just down the street, should I go there?"
        ],
        "technical": [
            "I'm not good with technology. My phone is very old.",
            "Can you wait? I need to find my glasses to see the screen properly.",
            "I don't know how to do that. Can you guide me step by step?"
        ],
        "lottery": [
            "Oh! I never win anything. Are you sure you have the right person?",
            "I don't remember entering any lottery. I don't gamble, you know.",
            "This sounds too good to be true. Is this real?"
        ],
        "romance": [
            "You are very kind. I don't get many compliments these days.",
            "That's very sweet. Tell me more about yourself.",
            "You sound like a nice person. Where are you from?"
        ],
        "phishing": [
            "I don't like giving personal information over the phone.",
            "Can I call you back on an official number? I want to be safe.",
            "My children told me to be careful about sharing my details."
        ],
        "impersonation": [
            "I didn't know {company} called people directly. Is this normal?",
            "Can I verify this with {company} directly? I want to be careful.",
            "I didn't request any support. Why are you calling me?"
        ]
    }
    
    def __init__(self):
        self._compiled_patterns = {}
        self._compile_patterns()
        logger.info("ReflexBrain initialized with {} patterns".format(len(self.PATTERNS)))
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance"""
        for name, config in self.PATTERNS.items():
            try:
                self._compiled_patterns[name] = {
                    "regex": re.compile(config["regex"], re.IGNORECASE),
                    "weight": config["weight"],
                    "category": config["category"]
                }
            except re.error as e:
                logger.error(f"Invalid regex pattern {name}: {e}")
    
    def analyze(self, message: str) -> List[PatternMatch]:
        """
        Analyze message for scam patterns.
        Returns list of matches sorted by confidence.
        """
        matches = []
        message_lower = message.lower()
        
        for name, config in self._compiled_patterns.items():
            regex = config["regex"]
            found = regex.search(message)
            
            if found:
                # Calculate contextual confidence
                confidence = config["weight"]
                
                # Boost confidence for multiple indicators
                if self._has_multiple_indicators(message_lower):
                    confidence = min(1.0, confidence + 0.1)
                
                matches.append(PatternMatch(
                    pattern_name=name,
                    confidence=confidence,
                    matched_text=found.group(),
                    category=config["category"],
                    suggested_action=self._get_suggested_action(config["category"])
                ))
        
        # Sort by confidence descending
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches
    
    def _has_multiple_indicators(self, message: str) -> bool:
        """Check if message has multiple scam indicators"""
        indicator_count = 0
        for config in self._compiled_patterns.values():
            if config["regex"].search(message):
                indicator_count += 1
                if indicator_count >= 3:
                    return True
        return False
    
    def _get_suggested_action(self, category: str) -> str:
        """Get recommended action based on category"""
        actions = {
            "financial": "extract_payment_details",
            "technical": "gather_remote_access_info",
            "threat": "document_threat_language",
            "pressure_tactic": "delay_and_extract",
            "lottery": "confirm_prize_structure",
            "romance": "build_trust_extract_background"
        }
        return actions.get(category, "continue_conversation")
    
    def generate_response(
        self, 
        matches: List[PatternMatch], 
        persona_context: Dict
    ) -> Tuple[str, Dict]:
        """
        Generate immediate response based on pattern matches.
        Returns (response, metadata).
        """
        if not matches:
            return None, {"used": False}
        
        # Use highest confidence match
        top_match = matches[0]
        category = top_match.category
        
        # Select appropriate response template
        if category in self.RESPONSES:
            import random
            template = random.choice(self.RESPONSES[category])
            
            # Personalize based on persona
            response = self._personalize_response(template, persona_context, matches)
            
            metadata = {
                "used": True,
                "brain": "reflex",
                "pattern": top_match.pattern_name,
                "confidence": top_match.confidence,
                "category": category,
                "action": top_match.suggested_action
            }
            
            return response, metadata
        
        return None, {"used": False}
    
    def _personalize_response(
        self, 
        template: str, 
        context: Dict,
        matches: List[PatternMatch]
    ) -> str:
        """Add persona-specific personalization"""
        response = template
        
        # Insert company name if impersonation detected
        if "{company}" in response:
            company = "the company"
            for match in matches:
                if match.category == "impersonation":
                    # Extract company name from match
                    company = match.matched_text.title()
                    break
            response = response.format(company=company)
        
        # Add age-appropriate hesitation markers
        age = context.get('age', 70)
        if age > 65 and "..." not in response:
            response = response.replace(".", "... ", 1)
        
        return response
    
    def get_urgency_score(self, message: str) -> float:
        """Calculate urgency score (0-1) for routing decision"""
        matches = self.analyze(message)
        if not matches:
            return 0.0
        
        # Weight by confidence and category
        urgency_weights = {
            "threat": 1.0,
            "financial": 0.9,
            "pressure_tactic": 0.8,
            "technical": 0.7,
            "lottery": 0.5,
            "romance": 0.3,
            "phishing": 0.6,
            "impersonation": 0.6
        }
        
        max_urgency = 0.0
        for match in matches:
            weight = urgency_weights.get(match.category, 0.5)
            score = match.confidence * weight
            max_urgency = max(max_urgency, score)
        
        return min(1.0, max_urgency)