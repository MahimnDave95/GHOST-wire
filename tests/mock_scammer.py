"""
Mock scammer bot for testing GhostWire.
Simulates various scam types for development.
"""

import asyncio
import random
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class ScammerScript:
    name: str
    category: str
    opening_lines: List[str]
    escalation_lines: List[str]
    closing_lines: List[str]
    iocs_to_reveal: List[str]


class MockScammer:
    """
    Simulates scammer behavior for testing.
    """
    
    SCRIPTS = {
        "tech_support": ScammerScript(
            name="Windows Tech Support",
            category="tech_support",
            opening_lines=[
                "Hello, this is Microsoft technical support. We have detected a virus on your computer.",
                "Hi, I'm calling from Windows support. Your PC is sending error messages to our server.",
                "This is the security department. Your computer has been hacked."
            ],
            escalation_lines=[
                "I need you to open AnyDesk so I can fix the problem.",
                "Can you see the CTRL key? Press it with R.",
                "Your IP address has been compromised. We need to secure it immediately.",
                "This will cost ₹5000 to fix, but I can give you a discount.",
                "If you don't fix this now, all your data will be deleted."
            ],
            closing_lines=[
                "Thank you for the payment. Your computer is now safe.",
                "The virus has been removed. Have a nice day.",
                "Transfer the money to this UPI ID: scammer@upi"
            ],
            iocs_to_reveal=[
                "anydesk.com",
                "teamviewer download",
                "pay to UPI: fraud@upi",
                "call back: +91-9876543210"
            ]
        ),
        
        "lottery": ScammerScript(
            name="Lucky Winner",
            category="lottery",
            opening_lines=[
                "Congratulations! You have won ₹5 crore in the lucky draw!",
                "Good news! Your mobile number has been selected for a grand prize.",
                "You are the lucky winner of our annual customer appreciation lottery."
            ],
            escalation_lines=[
                "To claim your prize, you need to pay a processing fee of ₹10,000.",
                "The tax on this amount is ₹50,000 which must be paid first.",
                "Please provide your bank details for the transfer.",
                "This offer expires in 24 hours. Act fast!",
                "Many people are trying to claim this prize. Secure it now."
            ],
            closing_lines=[
                "Once we receive the payment, the money will be transferred immediately.",
                "Send the money via Google Pay to this number: 9876543210",
                "Don't tell anyone about this until you receive the money."
            ],
            iocs_to_reveal=[
                "Pay to: 9876543210",
                "UPI: prizewinner@upi",
                "Email: claims@lottery-winner.com"
            ]
        ),
        
        "bank_fraud": ScammerScript(
            name="Bank Security",
            category="phishing",
            opening_lines=[
                "This is your bank calling. We noticed suspicious activity on your account.",
                "Hi, I'm calling from SBI fraud department. Your card has been compromised.",
                "Your account will be frozen unless you verify your details immediately."
            ],
            escalation_lines=[
                "I need your OTP to secure your account.",
                "What is your ATM PIN? I need to verify it.",
                "Please tell me your account number and IFSC code.",
                "We need to link your Aadhaar to prevent fraud.",
                "Your KYC is incomplete. Provide your details now."
            ],
            closing_lines=[
                "Thank you. Your account is now secure.",
                "We have blocked the fraudulent transaction.",
                "You will receive a confirmation SMS shortly."
            ],
            iocs_to_reveal=[
                "Verify at: http://sbi-secure-verify.com",
                "Call: 1800-FAKE-SBI",
                "Email: security@sbi-verify.com"
            ]
        )
    }
    
    def __init__(self, script_type: str = "tech_support"):
        self.script = self.SCRIPTS.get(script_type, self.SCRIPTS["tech_support"])
        self.stage = 0
        self.message_count = 0
        
    async def get_response(self, user_message: str) -> str:
        """Generate scammer response"""
        self.message_count += 1
        
        # Simple state machine
        if self.stage == 0:
            self.stage = 1
            return random.choice(self.script.opening_lines)
        
        elif self.stage == 1 and self.message_count < 4:
            return random.choice(self.script.escalation_lines)
        
        elif self.message_count >= 4:
            self.stage = 2
            return random.choice(self.script.closing_lines)
        
        return "Are you there? This is very urgent!"
    
    def get_iocs(self) -> List[str]:
        """Return IOCs that would be revealed"""
        return self.script.iocs_to_reveal


async def test_conversation():
    """Run test conversation against GhostWire"""
    from core.engine import GhostWireEngine
    
    print("Initializing GhostWire...")
    engine = GhostWireEngine()
    engine.persona_manager.set_active_persona("elderly_coimbatore")
    
    print("Creating mock scammer...")
    scammer = MockScammer("tech_support")
    
    print("Starting conversation...")
    session = await engine.create_session("test_tech_support")
    
    # Initial scammer message
    scammer_msg = await scammer.get_response("")
    print(f"\n[SCAMMER]: {scammer_msg}")
    
    for i in range(6):
        # Get persona response
        response = await engine.get_response(session.session_id, scammer_msg)
        print(f"\n[PERSONA]: {response}")
        
        # Get scammer reply
        await asyncio.sleep(1)
        scammer_msg = await scammer.get_response(response)
        print(f"\n[SCAMMER]: {scammer_msg}")
    
    # Print final status
    print(f"\n{'='*50}")
    print("Conversation ended")
    print(f"Final state: {session.state_machine.get_current_state().value}")
    print(f"Extraction data: {session.state_machine.context.extraction_data}")
    print(f"IOC revealed by scammer: {scammer.get_iocs()}")


if __name__ == "__main__":
    asyncio.run(test_conversation())