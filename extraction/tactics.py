"""
Tactic classification and scam type identification.
Maps conversations to known scam taxonomies.
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from collections import Counter


class ScamCategory(Enum):
    TECH_SUPPORT = "tech_support"
    PHISHING = "phishing"
    INVESTMENT = "investment_scam"
    ROMANCE = "romance_scam"
    LOTTERY = "lottery_scam"
    EXTORTION = "extortion"
    FAKE_CHARITY = "fake_charity"
    EMPLOYMENT = "fake_employment"
    UNKNOWN = "unknown"


@dataclass
class TacticProfile:
    """Scam tactic classification"""
    primary_category: ScamCategory
    secondary_categories: List[ScamCategory]
    confidence: float
    key_indicators: List[str]
    sophistication_score: int  # 1-10
    organization_level: str  # individual, small_group, organized_crime


class TacticClassifier:
    """
    Classifies scam tactics based on conversation patterns.
    Uses rule-based scoring with ML enhancement potential.
    """
    
    # Category indicators
    CATEGORY_INDICATORS = {
        ScamCategory.TECH_SUPPORT: {
            "keywords": [
                "virus", "malware", "infected", "security", "microsoft", 
                "apple", "windows", "mac", "remote access", "anydesk", 
                "teamviewer", "slow computer", "hacked"
            ],
            "weight": 1.0
        },
        ScamCategory.PHISHING: {
            "keywords": [
                "verify account", "update details", "suspended", "login", 
                "password", "OTP", "one time password", "bank account", 
                "KYC", "PAN card", "Aadhaar"
            ],
            "weight": 1.0
        },
        ScamCategory.INVESTMENT: {
            "keywords": [
                "returns", "profit", "investment", "bitcoin", "crypto", 
                "trading", "forex", "guaranteed returns", "double your money",
                "scheme", "portfolio", "stocks", "shares"
            ],
            "weight": 1.0
        },
        ScamCategory.ROMANCE: {
            "keywords": [
                "love", "dear", "sweetheart", "beautiful", "marry", 
                "relationship", "destiny", "god sent", "soulmate",
                "military", "overseas", "stuck", "need money"
            ],
            "weight": 1.0
        },
        ScamCategory.LOTTERY: {
            "keywords": [
                "won", "winner", "prize", "lottery", "jackpot", "lucky draw",
                "selected", "random", "million", "crore", "claim prize",
                "processing fee", "tax on prize"
            ],
            "weight": 1.0
        },
        ScamCategory.EXTORTION: {
            "keywords": [
                "arrest", "police", "court", "warrant", "legal action",
                "prosecution", "crime", "federal", "investigation",
                "pay fine", "settle", "out of court"
            ],
            "weight": 1.0
        }
    }
    
    def classify(self, conversation_text: str) -> TacticProfile:
        """
        Classify scam type from conversation text.
        """
        text_lower = conversation_text.lower()
        scores = Counter()
        
        # Score each category
        for category, data in self.CATEGORY_INDICATORS.items():
            score = 0
            found_indicators = []
            
            for keyword in data["keywords"]:
                if keyword in text_lower:
                    score += data["weight"]
                    found_indicators.append(keyword)
            
            scores[category] = score
        
        # Determine primary and secondary
        if not scores:
            return TacticProfile(
                primary_category=ScamCategory.UNKNOWN,
                secondary_categories=[],
                confidence=0.0,
                key_indicators=[],
                sophistication_score=5,
                organization_level="unknown"
            )
        
        top_categories = scores.most_common(3)
        primary = top_categories[0][0]
        primary_score = top_categories[0][1]
        
        # Calculate confidence
        total_score = sum(scores.values())
        confidence = primary_score / total_score if total_score > 0 else 0
        
        # Determine sophistication
        soph_score = self._calculate_sophistication(text_lower, primary)
        
        # Determine organization level
        org_level = self._determine_organization(text_lower)
        
        return TacticProfile(
            primary_category=primary,
            secondary_categories=[c[0] for c in top_categories[1:] if c[1] > 0],
            confidence=min(1.0, confidence),
            key_indicators=[kw for kw in self.CATEGORY_INDICATORS[primary]["keywords"] 
                          if kw in text_lower][:5],
            sophistication_score=soph_score,
            organization_level=org_level
        )
    
    def _calculate_sophistication(self, text: str, category: ScamCategory) -> int:
        """Estimate operation sophistication (1-10)"""
        score = 5  # Baseline
        
        # Indicators of sophistication
        if "custom domain" in text or "professional website" in text:
            score += 2
        if "call center" in text or "supervisor" in text:
            score += 1
        if "script" in text or "follow the process" in text:
            score += 1
        if len(set(line.strip() for line in text.split('\n'))) < 5:
            score -= 2  # Repetitive = less sophisticated
        
        # Grammar and spelling (proxy for sophistication)
        common_typos = ['recieve', 'seperate', 'occured', 'govt', 'pls', 'ur']
        typo_count = sum(1 for typo in common_typos if typo in text)
        if typo_count > 3:
            score -= 1
        
        return max(1, min(10, score))
    
    def _determine_organization(self, text: str) -> str:
        """Determine if individual or organized operation"""
        org_indicators = [
            "call center", "supervisor", "manager", "escalate", 
            "department", "team", "office", "shift"
        ]
        individual_indicators = [
            "i personally", "my own", "me and my", "i need this money",
            "help my family", "my situation"
        ]
        
        org_score = sum(1 for ind in org_indicators if ind in text)
        ind_score = sum(1 for ind in individual_indicators if ind in text)
        
        if org_score >= 2:
            return "organized_crime" if org_score >= 4 else "small_group"
        elif ind_score >= 2:
            return "individual"
        return "unknown"
    
    def get_mitigation_advice(self, profile: TacticProfile) -> List[str]:
        """Generate advice based on scam type"""
        advice_map = {
            ScamCategory.TECH_SUPPORT: [
                "Never grant remote access to unsolicited callers",
                "Legitimate companies don't call about computer viruses",
                "Hang up and contact company directly through official website"
            ],
            ScamCategory.PHISHING: [
                "Don't click links in unsolicited messages",
                "Verify directly with bank/organization",
                "Check URL carefully for misspellings"
            ],
            ScamCategory.INVESTMENT: [
                "Guaranteed high returns are always scams",
                "Verify SEBI registration of investment advisors",
                "Never invest in schemes you don't understand"
            ],
            ScamCategory.ROMANCE: [
                "Never send money to someone you haven't met",
                "Reverse image search profile photos",
                "Be suspicious of rapid relationship progression"
            ],
            ScamCategory.LOTTERY: [
                "You can't win lotteries you didn't enter",
                "Legitimate lotteries don't require fees to claim",
                "Verify through official lottery website"
            ],
            ScamCategory.EXTORTION: [
                "Government agencies don't demand payment over phone",
                "Ask for written notice",
                "Contact agency directly through official channels"
            ]
        }
        
        return advice_map.get(profile.primary_category, ["Be cautious", "Verify independently"])