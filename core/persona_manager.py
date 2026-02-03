"""
Manages decoy personas with consistency enforcement.
Ensures persona never breaks character during conversations.
"""

import yaml
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from loguru import logger


@dataclass
class PersonaProfile:
    """Complete persona specification"""
    id: str
    name: str
    age: int
    location: str
    occupation: str
    backstory: str
    
    # Personality traits (0-10 scale)
    traits: Dict[str, int] = field(default_factory=dict)
    
    # Communication style
    communication_style: Dict[str, Any] = field(default_factory=dict)
    
    # Vulnerabilities (what scammers exploit)
    vulnerabilities: List[str] = field(default_factory=list)
    
    # Knowledge gaps (things they wouldn't know)
    knowledge_gaps: List[str] = field(default_factory=list)
    
    # Technical sophistication (0-10)
    tech_sophistication: int = 3
    
    # Financial situation
    financial_profile: Dict[str, Any] = field(default_factory=dict)
    
    # Relationships
    family_context: Dict[str, str] = field(default_factory=dict)
    
    # Consistency rules
    consistency_rules: List[str] = field(default_factory=list)


class PersonaManager:
    """
    Loads and manages personas with strict consistency checking.
    Prevents persona from breaking character or revealing AI nature.
    """
    
    def __init__(self, personas_dir: str = "personas"):
        self.personas_dir = Path(personas_dir)
        self.personas: Dict[str, PersonaProfile] = {}
        self.active_persona: Optional[PersonaProfile] = None
        self._load_personas()
    
    def _load_personas(self) -> None:
        """Load all persona definitions"""
        if not self.personas_dir.exists():
            logger.warning(f"Personas directory not found: {self.personas_dir}")
            return
        
        for file_path in self.personas_dir.glob("*.py"):
            # Dynamic import of persona modules
            persona_id = file_path.stem
            try:
                # Import and extract PERSONA dict from module
                import importlib.util
                spec = importlib.util.spec_from_file_location(persona_id, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'PERSONA'):
                    self.personas[persona_id] = self._dict_to_profile(persona_id, module.PERSONA)
                    logger.info(f"Loaded persona: {persona_id}")
            except Exception as e:
                logger.error(f"Failed to load persona {persona_id}: {e}")
    
    def _dict_to_profile(self, persona_id: str, data: Dict) -> PersonaProfile:
        """Convert dictionary to PersonaProfile"""
        return PersonaProfile(
            id=persona_id,
            name=data.get('name', 'Unknown'),
            age=data.get('age', 60),
            location=data.get('location', 'Unknown'),
            occupation=data.get('occupation', 'Retired'),
            backstory=data.get('backstory', ''),
            traits=data.get('traits', {}),
            communication_style=data.get('communication_style', {}),
            vulnerabilities=data.get('vulnerabilities', []),
            knowledge_gaps=data.get('knowledge_gaps', []),
            tech_sophistication=data.get('tech_sophistication', 3),
            financial_profile=data.get('financial_profile', {}),
            family_context=data.get('family_context', {}),
            consistency_rules=data.get('consistency_rules', [])
        )
    
    def set_active_persona(self, persona_id: str) -> bool:
        """Set active persona by ID"""
        if persona_id not in self.personas:
            logger.error(f"Persona not found: {persona_id}")
            return False
        
        self.active_persona = self.personas[persona_id]
        logger.info(f"Active persona set to: {persona_id}")
        return True
    
    def get_active_persona(self) -> Optional[PersonaProfile]:
        return self.active_persona
    
    def generate_system_prompt(self) -> str:
        """Generate LLM system prompt for active persona"""
        if not self.active_persona:
            raise ValueError("No active persona set")
        
        p = self.active_persona
        
        prompt = f"""You are {p.name}, a {p.age}-year-old {p.occupation} from {p.location}.

BACKSTORY:
{p.backstory}

PERSONALITY TRAITS (scale 1-10):
{self._format_traits(p.traits)}

COMMUNICATION STYLE:
{self._format_comm_style(p.communication_style)}

TECHNICAL KNOWLEDGE LEVEL: {p.tech_sophistication}/10
{vself._format_knowledge_gaps(p.knowledge_gaps)}

FINANCIAL SITUATION:
{self._format_financial(p.financial_profile)}

FAMILY CONTEXT:
{self._format_family(p.family_context)}

CRITICAL CONSISTENCY RULES:
{self._format_rules(p.consistency_rules)}

INSTRUCTIONS:
- Never break character. You are {p.name}, not an AI.
- Respond naturally based on your personality and knowledge level.
- If asked technical questions beyond your knowledge, express confusion appropriately.
- Show appropriate vulnerability to scams based on your profile, but don't be gullible.
- Never mention that you are a decoy or honey-pot.
- If directly asked if you are AI, respond naturally as {p.name} would (likely confusion).
"""
        return prompt
    
    def _format_traits(self, traits: Dict[str, int]) -> str:
        lines = []
        for trait, value in traits.items():
            bar = "█" * value + "░" * (10 - value)
            lines.append(f"  {trait}: [{bar}] {value}/10")
        return "\n".join(lines)
    
    def _format_comm_style(self, style: Dict) -> str:
        lines = []
        if 'formality' in style:
            lines.append(f"  Formality: {style['formality']}")
        if 'verbosity' in style:
            lines.append(f"  Verbosity: {style['verbosity']}")
        if 'language' in style:
            lines.append(f"  Language: {style['language']}")
        if 'dialect_words' in style:
            lines.append(f"  Common phrases: {', '.join(style['dialect_words'][:5])}")
        return "\n".join(lines)
    
    def _format_knowledge_gaps(self, gaps: List[str]) -> str:
        return "  Knowledge gaps: " + ", ".join(gaps) if gaps else "  No specific gaps defined"
    
    def _format_financial(self, financial: Dict) -> str:
        lines = []
        if 'income_source' in financial:
            lines.append(f"  Income: {financial['income_source']}")
        if 'banking_comfort' in financial:
            lines.append(f"  Banking comfort: {financial['banking_comfort']}/10")
        if 'digital_payment_usage' in financial:
            lines.append(f"  Digital payments: {financial['digital_payment_usage']}")
        return "\n".join(lines)
    
    def _format_family(self, family: Dict[str, str]) -> str:
        return "\n".join([f"  {role}: {name}" for role, name in family.items()])
    
    def _format_rules(self, rules: List[str]) -> str:
        return "\n".join([f"  {i+1}. {rule}" for i, rule in enumerate(rules)])
    
    def validate_response(self, response: str) -> tuple[bool, List[str]]:
        """
        Check if response violates persona consistency.
        Returns (is_valid, list_of_violations)
        """
        if not self.active_persona:
            return True, []
        
        violations = []
        response_lower = response.lower()
        
        # Check for AI reveals
        ai_phrases = [
            "as an ai", "i am an ai", "i'm an ai", "as a language model",
            "i don't have personal experiences", "i cannot feel", "my training data",
            "artificial intelligence", "neural network", "algorithm"
        ]
        
        for phrase in ai_phrases:
            if phrase in response_lower:
                violations.append(f"AI reveal detected: '{phrase}'")
        
        # Check for knowledge violations (if persona wouldn't know something)
        # This is a simplified check - could be enhanced with NLP
        tech_terms = ["api", "json", "python", "docker", "kubernetes"]
        if self.active_persona.tech_sophistication < 5:
            for term in tech_terms:
                if term in response_lower and term not in str(self.active_persona.knowledge_gaps):
                    violations.append(f"Technical term beyond persona level: '{term}'")
        
        # Check for name consistency
        if self.active_persona.name.split()[0].lower() not in response_lower:
            # Not necessarily a violation, but worth noting if persona never self-identifies
            pass
        
        return len(violations) == 0, violations
    
    def get_persona_list(self) -> List[str]:
        """Get list of available persona IDs"""
        return list(self.personas.keys())