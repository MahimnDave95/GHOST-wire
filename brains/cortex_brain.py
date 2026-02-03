"""
Cortex Brain - Sophisticated LLM-based reasoning for complex scenarios.
Uses local models via Ollama or HuggingFace.
"""

import json
import re
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass
import asyncio
from loguru import logger


@dataclass
class LLMResponse:
    content: str
    model_used: str
    latency_ms: float
    tokens_used: int
    confidence: float


class LocalLLMClient:
    """
    Client for local LLM inference.
    Supports Ollama (preferred) and HuggingFace fallback.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.provider = config.get('provider', 'ollama')
        self.model = config.get('model', 'llama2:13b')
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 512)
        self.timeout = config.get('timeout', 30)
        
        self._ollama_available = None
        self._hf_pipeline = None
        
        logger.info(f"LocalLLM initialized with provider: {self.provider}, model: {self.model}")
    
    async def check_ollama(self) -> bool:
        """Check if Ollama server is running"""
        if self._ollama_available is not None:
            return self._ollama_available
            
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    self._ollama_available = resp.status == 200
                    if self._ollama_available:
                        logger.info("Ollama server is available")
                    return self._ollama_available
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._ollama_available = False
            return False
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate text using available local LLM.
        """
        import time
        start_time = time.time()
        
        # Try Ollama first
        if await self.check_ollama():
            return await self._generate_ollama(prompt, system_prompt)
        
        # Fallback to HuggingFace
        if self.config.get('fallback', {}).get('enabled', True):
            return await self._generate_hf(prompt, system_prompt)
        
        raise RuntimeError("No LLM backend available")
    
    async def _generate_ollama(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate using Ollama API"""
        import aiohttp
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(f"Ollama error: {error_text}")
                
                result = await resp.json()
                
                latency = (time.time() - start_time) * 1000
                
                return LLMResponse(
                    content=result.get('response', ''),
                    model_used=f"ollama:{self.model}",
                    latency_ms=latency,
                    tokens_used=result.get('eval_count', 0),
                    confidence=0.8  # Ollama doesn't provide logprobs
                )
    
    async def _generate_hf(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate using HuggingFace Transformers (local)"""
        if self._hf_pipeline is None:
            self._init_hf_pipeline()
        
        # Run in thread pool to not block
        loop = asyncio.get_event_loop()
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        result = await loop.run_in_executor(
            None,
            lambda: self._hf_pipeline(
                full_prompt,
                max_length=self.max_tokens,
                temperature=self.temperature,
                do_sample=True,
                return_full_text=False
            )
        )
        
        latency = (time.time() - start_time) * 1000
        
        generated_text = result[0]['generated_text'] if result else ""
        
        # Clean up common HF artifacts
        generated_text = self._clean_hf_output(generated_text)
        
        return LLMResponse(
            content=generated_text,
            model_used=f"hf:{self.config.get('fallback', {}).get('model', 'unknown')}",
            latency_ms=latency,
            tokens_used=len(generated_text.split()),  # Approximate
            confidence=0.7
        )
    
    def _init_hf_pipeline(self):
        """Initialize HuggingFace pipeline"""
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        
        model_name = self.config.get('fallback', {}).get('model', 'microsoft/DialoGPT-medium')
        
        logger.info(f"Loading HF model: {model_name}")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype="auto"
        )
        
        self._hf_pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer
        )
    
    def _clean_hf_output(self, text: str) -> str:
        """Clean up HuggingFace generation artifacts"""
        # Remove prompt echo
        lines = text.split('\n')
        if len(lines) > 1:
            text = '\n'.join(lines[1:])
        
        # Cut off at natural ending
        end_markers = ['.', '!', '?', '\n']
        for marker in end_markers:
            if marker in text:
                idx = text.rfind(marker, 0, 200)  # Look in first 200 chars
                if idx > 50:  # Ensure minimum length
                    text = text[:idx+1]
                    break
        
        return text.strip()


class CortexBrain:
    """
    Sophisticated reasoning brain using local LLMs.
    Handles complex social engineering and extraction scenarios.
    """
    
    def __init__(self, config: Dict):
        self.llm = LocalLLMClient(config)
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.max_history = 10
        
        logger.info("CortexBrain initialized")
    
    async def generate_response(
        self,
        message: str,
        session_id: str,
        persona_system_prompt: str,
        state_context: Dict,
        extraction_goals: List[str]
    ) -> tuple[str, Dict]:
        """
        Generate sophisticated response using LLM.
        """
        # Build conversation context
        history = self._get_history(session_id)
        
        # Construct prompt
        prompt = self._build_prompt(
            message=message,
            history=history,
            state=state_context.get('current_state', 'unknown'),
            extraction_goals=extraction_goals
        )
        
        # Generate
        try:
            llm_response = await self.llm.generate(prompt, persona_system_prompt)
            
            # Update history
            self._update_history(session_id, message, llm_response.content)
            
            # Extract metadata
            metadata = {
                "used": True,
                "brain": "cortex",
                "model": llm_response.model_used,
                "latency_ms": llm_response.latency_ms,
                "tokens": llm_response.tokens_used,
                "confidence": llm_response.confidence
            }
            
            return llm_response.content, metadata
            
        except Exception as e:
            logger.error(f"Cortex generation failed: {e}")
            # Fallback to safe response
            return self._fallback_response(), {"used": False, "error": str(e)}
    
    def _build_prompt(
        self,
        message: str,
        history: List[Dict],
        state: str,
        extraction_goals: List[str]
    ) -> str:
        """Build structured prompt for LLM"""
        
        # Recent conversation context
        recent_exchanges = []
        for h in history[-5:]:  # Last 5 exchanges
            recent_exchanges.append(f"Scammer: {h['input']}")
            recent_exchanges.append(f"You: {h['output']}")
        
        context_str = "\n".join(recent_exchanges) if recent_exchanges else "This is the start of the conversation."
        
        extraction_str = ""
        if extraction_goals:
            extraction_str = f"\nINTELLIGENCE GOALS (gather subtly):\n" + "\n".join([f"- {g}" for g in extraction_goals])
        
        prompt = f"""CONVERSATION STATE: {state}

RECENT CONTEXT:
{context_str}

CURRENT MESSAGE FROM SCAMMER:
"{message}"
{extraction_str}

INSTRUCTIONS:
- Respond naturally as your persona would.
- Stay in character at all times.
- If they're asking for information, be cautious but gradually cooperative to gain trust.
- Ask clarifying questions to extract more details about their operation.
- Never reveal you are AI or a decoy.
- Keep responses concise (1-3 sentences typical for chat).

YOUR RESPONSE:"""
        
        return prompt
    
    def _get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session"""
        return self.conversation_history.get(session_id, [])
    
    def _update_history(self, session_id: str, input_msg: str, output_msg: str) -> None:
        """Update conversation history"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            "input": input_msg,
            "output": output_msg,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Trim history
        if len(self.conversation_history[session_id]) > self.max_history:
            self.conversation_history[session_id] = self.conversation_history[session_id][-self.max_history:]
    
    def _fallback_response(self) -> str:
        """Safe fallback if LLM fails"""
        fallbacks = [
            "I'm sorry, I didn't catch that. Could you say it again?",
            "My connection is a bit slow. Can you repeat that?",
            "I'm not sure I understand. Can you explain it differently?",
            "One moment please, I'm trying to understand."
        ]
        import random
        return random.choice(fallbacks)
    
    async def analyze_tactics(self, conversation_text: str) -> Dict:
        """
        Post-conversation analysis of scammer tactics.
        """
        prompt = f"""Analyze the following scam conversation and identify:
1. Scam type/category
2. Specific tactics used
3. Psychological manipulation techniques
4. Indicators of organized operation vs individual

CONVERSATION:
{conversation_text[:2000]}  # Limit length

Provide analysis in JSON format:
{{
    "scam_type": "...", 
    "tactics": ["...", "..."],
    "psychological_triggers": ["...", "..."],
    "organization_level": "high/medium/low",
    "sophistication_score": 1-10
}}"""

        try:
            response = await self.llm.generate(prompt)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Tactic analysis failed: {e}")
        
        return {"error": "analysis_failed"}