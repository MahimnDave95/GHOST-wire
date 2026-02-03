"""
Intelligence extraction engine - Identifies IOCs and scammer infrastructure.
Uses regex, NLP, and contextual analysis.
"""

import re
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urlparse
import hashlib
from loguru import logger


@dataclass
class ExtractedIOC:
    """Individual Indicator of Compromise"""
    ioc_type: str  # phone, email, upi, bank_account, crypto_wallet, url, ip
    value: str
    confidence: float
    context: str
    first_seen: datetime
    source_conversation: str
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "first_seen": self.first_seen.isoformat()
        }


class ExtractionEngine:
    """
    Extracts structured intelligence from conversations.
    Identifies payment mechanisms, infrastructure, and tactics.
    """
    
    # Regex patterns for IOC extraction
    PATTERNS = {
        "phone_india": {
            "regex": r'(?:\+91|0)?[ -]?[6-9]\d{9}',
            "type": "phone",
            "confidence": 0.9
        },
        "phone_international": {
            "regex": r'\+\d{1,3}[ -]?\d{6,12}',
            "type": "phone",
            "confidence": 0.8
        },
        "email": {
            "regex": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "type": "email",
            "confidence": 0.95
        },
        "upi_id": {
            "regex": r'[a-zA-Z0-9._-]+@[a-zA-Z]{3,}',  # Basic UPI pattern
            "type": "upi",
            "confidence": 0.85
        },
        "bank_account": {
            "regex": r'\b\d{9,18}\b',  # Indian account numbers
            "type": "bank_account",
            "confidence": 0.6  # Lower confidence - many false positives
        },
        "ifsc_code": {
            "regex": r'[A-Z]{4}0[A-Z0-9]{6}',
            "type": "ifsc",
            "confidence": 0.95
        },
        "crypto_btc": {
            "regex": r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|\bbc1[a-z0-9]{39,59}\b',
            "type": "crypto_btc",
            "confidence": 0.95
        },
        "crypto_eth": {
            "regex": r'\b0x[a-fA-F0-9]{40}\b',
            "type": "crypto_eth",
            "confidence": 0.95
        },
        "url": {
            "regex": r'https?://[^\s<>\"{}|\\^`\[\]]+',
            "type": "url",
            "confidence": 0.9
        },
        "ip_address": {
            "regex": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "type": "ip",
            "confidence": 0.8
        }
    }
    
    def __init__(self):
        self.compiled_patterns = {}
        self._compile_patterns()
        self.extracted_iocs: Set[str] = set()  # Deduplication
        
        logger.info("ExtractionEngine initialized")
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns"""
        for name, config in self.PATTERNS.items():
            try:
                self.compiled_patterns[name] = {
                    "regex": re.compile(config["regex"]),
                    "type": config["type"],
                    "confidence": config["confidence"]
                }
            except re.error as e:
                logger.error(f"Invalid pattern {name}: {e}")
    
    async def extract(
        self,
        incoming: str,
        outgoing: str,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Main extraction method. Called after each exchange.
        """
        combined_text = f"{incoming} {outgoing}"
        context = f"Exchange in conversation {conversation_id}"
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "conversation_id": conversation_id,
            "iocs": [],
            "tactics": [],
            "metadata": {}
        }
        
        # Extract IOCs
        iocs = self._extract_iocs(combined_text, context, conversation_id)
        results["iocs"] = [ioc.to_dict() for ioc in iocs]
        
        # Extract tactics
        tactics = self._extract_tactics(incoming)
        results["tactics"] = tactics
        
        # Extract metadata
        results["metadata"] = self._extract_metadata(incoming, outgoing)
        
        return results if (iocs or tactics) else None
    
    def _extract_iocs(
        self,
        text: str,
        context: str,
        conversation_id: str
    ) -> List[ExtractedIOC]:
        """Extract all IOCs from text"""
        iocs = []
        
        for pattern_name, config in self.compiled_patterns.items():
            matches = config["regex"].findall(text)
            
            for match in matches:
                # Handle tuple returns from regex groups
                if isinstance(match, tuple):
                    match = match[0]
                
                match_str = str(match).strip()
                
                # Deduplication
                match_hash = hashlib.md5(match_str.lower().encode()).hexdigest()
                if match_hash in self.extracted_iocs:
                    continue
                self.extracted_iocs.add(match_hash)
                
                # Validate and clean
                cleaned = self._clean_ioc(config["type"], match_str)
                if not cleaned:
                    continue
                
                ioc = ExtractedIOC(
                    ioc_type=config["type"],
                    value=cleaned,
                    confidence=config["confidence"],
                    context=context[:200],  # Truncate context
                    first_seen=datetime.now(),
                    source_conversation=conversation_id
                )
                iocs.append(ioc)
                
                logger.info(f"Extracted {config['type']}: {cleaned[:20]}...")
        
        return iocs
    
    def _clean_ioc(self, ioc_type: str, value: str) -> Optional[str]:
        """Clean and validate IOC"""
        value = value.strip()
        
        if ioc_type == "phone":
            # Normalize phone number
            digits = re.sub(r'\D', '', value)
            if len(digits) == 10:
                return f"+91{digits}"
            elif len(digits) == 12 and digits.startswith('91'):
                return f"+{digits}"
            return None
            
        elif ioc_type == "upi":
            # Validate UPI format
            if '@' in value and len(value) > 5:
                return value.lower()
            return None
            
        elif ioc_type == "url":
            try:
                parsed = urlparse(value)
                if parsed.scheme and parsed.netloc:
                    return value.lower()
            except:
                pass
            return None
            
        elif ioc_type in ["crypto_btc", "crypto_eth"]:
            return value
        
        return value
    
    def _extract_tactics(self, message: str) -> List[Dict]:
        """Identify scam tactics from message"""
        tactics = []
        msg_lower = message.lower()
        
        # Urgency tactics
        urgency_indicators = [
            ("immediate_action", ["immediately", "right now", "urgent", "asap", "hurry"]),
            ("time_pressure", ["24 hours", "today only", "last chance", "deadline", "expires"]),
            ("scarcity", ["limited spots", "only few left", "exclusive offer", "special selection"])
        ]
        
        for tactic_name, keywords in urgency_indicators:
            if any(kw in msg_lower for kw in keywords):
                tactics.append({
                    "tactic": tactic_name,
                    "category": "urgency",
                    "confidence": 0.8,
                    "indicators_found": [kw for kw in keywords if kw in msg_lower]
                })
        
        # Authority abuse
        authority_indicators = [
            ("government_impersonation", ["government", "ministry", "tax department", " RBI ", "TRAI"]),
            ("bank_impersonation", ["bank manager", "account frozen", "suspicious transaction", "KYC"]),
            ("police_threat", ["police", "arrest warrant", "legal action", "court", "fir"])
        ]
        
        for tactic_name, keywords in authority_indicators:
            if any(kw in msg_lower for kw in keywords):
                tactics.append({
                    "tactic": tactic_name,
                    "category": "authority_abuse",
                    "confidence": 0.85,
                    "indicators_found": [kw for kw in keywords if kw in msg_lower]
                })
        
        # Social engineering
        social_indicators = [
            ("trust_building", ["trust me", "don't worry", "i'm here to help", "your friend"]),
            ("relationship_exploit", ["your son", "your family", "emergency", "accident", "hospital"]),
            ("reciprocity", ["free gift", "as a favor", "special for you", "only for you"])
        ]
        
        for tactic_name, keywords in social_indicators:
            if any(kw in msg_lower for kw in keywords):
                tactics.append({
                    "tactic": tactic_name,
                    "category": "social_engineering",
                    "confidence": 0.75,
                    "indicators_found": [kw for kw in keywords if kw in msg_lower]
                })
        
        return tactics
    
    def _extract_metadata(self, incoming: str, outgoing: str) -> Dict:
        """Extract conversation metadata"""
        return {
            "incoming_length": len(incoming),
            "outgoing_length": len(outgoing),
            "incoming_language": self._detect_language(incoming),
            "sentiment_incoming": self._estimate_sentiment(incoming),
            "complexity_score": len(incoming.split()) / 10  # Words / 10
        }
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        # Check for common Tamil words
        tamil_words = ['amma', 'anna', 'nandri', 'seri', 'illai', 'aama', 'illa']
        text_lower = text.lower()
        
        tamil_count = sum(1 for word in tamil_words if word in text_lower)
        if tamil_count >= 2:
            return "ta-en"  # Tamil-English mix
        
        # Check for Hindi
        hindi_words = ['hai', 'ji', 'beta', 'bhai', 'dhanyavad']
        hindi_count = sum(1 for word in hindi_words if word in text_lower)
        if hindi_count >= 2:
            return "hi-en"
        
        return "en"
    
    def _estimate_sentiment(self, text: str) -> str:
        """Simple sentiment estimation"""
        positive = ['good', 'great', 'thank', 'happy', 'please', 'help', 'kind']
        negative = ['bad', 'stupid', 'idiot', 'fool', 'hurry', 'now', 'urgent', 'problem']
        threatening = ['arrest', 'police', 'legal', 'court', 'punish', 'fine', 'penalty']
        
        text_lower = text.lower()
        
        threat_count = sum(1 for word in threatening if word in text_lower)
        if threat_count > 0:
            return "threatening"
        
        neg_count = sum(1 for word in negative if word in text_lower)
        pos_count = sum(1 for word in positive if word in text_lower)
        
        if neg_count > pos_count:
            return "negative"
        elif pos_count > neg_count:
            return "positive"
        return "neutral"
    
    def generate_report(self, conversation_id: str) -> Dict:
        """Generate final intelligence report"""
        # This would aggregate all extractions from a conversation
        return {
            "conversation_id": conversation_id,
            "generated_at": datetime.now().isoformat(),
            "summary": "Extraction report placeholder"
        }