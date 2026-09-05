"""
RECLAIM Hardware Authorization Service
Person 3: Hardware responsibility

Flow:
Person 2: Risk Engine returns decision "TRIGGER_RECLAIM" with challenge_id & challenge_payload
   │
   ▼
Person 3: Prompts ESP32 Hardware Authorization flow
          ESP32 displays challenge_id & signs challenge_payload with private key
   │
   ├──────► IF Authorization PASSES ──► Process Transfer (Resets failed attempts)
   │
   └──────► IF Failed Attempt:
               │ Count < 3 ──► Block transaction & warn remaining attempts
               │ Count >= 3 ──► Trigger Person 4 (FREEZE MODE & Account Recovery)
"""

from typing import Optional, Callable, Dict, Any
from .types import (
    TransactionPayload,
    RiskLevel,
    RiskDecision,
    HardwareAuthRequest,
    VerificationResult,
    AuthorizationStatus,
)
from .hardware_client import HardwareClient
from .signature_verifier import SignatureVerifier


class HardwareAuthorizationService:
    def __init__(
        self,
        hardware_client: HardwareClient,
        signature_verifier: SignatureVerifier,
        person4_compromise_handler: Optional[Callable[[TransactionPayload, VerificationResult], None]] = None,
        max_allowed_failed_attempts: int = 3,
    ):
        self.hardware_client = hardware_client
        self.signature_verifier = signature_verifier
        self.person4_compromise_handler = person4_compromise_handler
        self.max_allowed_failed_attempts = max_allowed_failed_attempts
        
        # User attempt counters: sender -> failed_attempts_count
        self.user_failed_attempts: Dict[str, int] = {}

    def get_failed_attempts(self, user_id: str) -> int:
        return self.user_failed_attempts.get(user_id, 0)

    def reset_failed_attempts(self, user_id: str):
        self.user_failed_attempts[user_id] = 0

    def process_transaction_authorization(self, tx: TransactionPayload) -> VerificationResult:
        """
        Main entry point processing Person 2's Risk Engine payload ("TRIGGER_RECLAIM").
        """
        user_id = tx.sender
        current_fails = self.get_failed_attempts(user_id)

        # Check if user is already locked due to 3 prior failed attempts
        if current_fails >= self.max_allowed_failed_attempts:
            reason = f"Account '{user_id}' is locked! 3 failed hardware authorization attempts exceeded. Freeze Mode Active."
            print(f"\n[PERSON 3 HARDWARE AUTH] {reason}")
            res = VerificationResult(
                is_valid=False,
                status=AuthorizationStatus.FREEZE_MODE_TRIGGERED,
                reason=reason,
                failed_attempts_count=current_fails,
                details={"user_id": user_id, "action": "PERSON_4_FREEZE_MODE"},
            )
            if self.person4_compromise_handler:
                self.person4_compromise_handler(tx, res)
            return res

        # Bypass hardware check only if Person 2 decision is ALLOW and Risk is LOW
        if tx.risk_decision == RiskDecision.ALLOW.value and tx.risk_level == RiskLevel.LOW:
            return VerificationResult(
                is_valid=True,
                status=AuthorizationStatus.APPROVED,
                reason="Low risk transaction does not require hardware authorization.",
                details={"risk_level": tx.risk_level.value},
            )

        # Person 2 Trigger Reclaim Flow
        risk_factors_str = ", ".join(tx.risk_factors) if tx.risk_factors else "high_risk_transfer"
        print(f"\n[PERSON 2 RISK ENGINE] Decision: '{tx.risk_decision}' | Challenge ID: '{tx.challenge_id}'")
        print(f"                      Challenge Payload: '{tx.challenge_payload}' | Risk Factors: [{risk_factors_str}]")
        print(f"[PERSON 3 HARDWARE AUTH] Forwarding Challenge to ESP32 hardware device (Attempt {current_fails + 1}/{self.max_allowed_failed_attempts})...")

        auth_req = HardwareAuthRequest(
            transaction_id=tx.transaction_id,
            amount=tx.amount,
            recipient=tx.recipient,
            nonce=tx.nonce,
            timestamp=tx.timestamp,
            challenge_id=tx.challenge_id,
            challenge_payload=tx.challenge_payload,
        )

        # Request signature from physical ESP32 or simulator
        hw_response = self.hardware_client.request_hardware_signature(auth_req)

        # Verify signature, nonces, and challenge integrity
        verification_result = self.signature_verifier.verify_hardware_signature(tx, hw_response)

        if verification_result.is_valid:
            # RESET failed attempts counter on SUCCESS
            self.reset_failed_attempts(user_id)
            verification_result.failed_attempts_count = 0
            print(f"[RECLAIM SYSTEM] APPROVE - Challenge '{tx.challenge_id}' verified successfully! Process transfer for '{tx.transaction_id}'.")
            return verification_result

        # Handle Hardware Authorization FAILURE
        current_fails += 1
        self.user_failed_attempts[user_id] = current_fails
        verification_result.failed_attempts_count = current_fails

        if current_fails >= self.max_allowed_failed_attempts:
            verification_result.status = AuthorizationStatus.FREEZE_MODE_TRIGGERED
            verification_result.reason += f" [STRIKE {current_fails}/{self.max_allowed_failed_attempts} - FREEZE MODE TRIGGERED]"
            print(f"[RECLAIM SYSTEM] FREEZE MODE - 3 Failed Hardware Authorization Attempts reached for '{user_id}'!")
            
            # Trigger Person 4 Compromise & Freeze Protocol
            if self.person4_compromise_handler:
                print("[PERSON 3 -> PERSON 4] Triggering Person 4 (Account Freeze & Security Recovery Protocol).")
                self.person4_compromise_handler(tx, verification_result)
        else:
            verification_result.status = AuthorizationStatus.BLOCKED
            remaining = self.max_allowed_failed_attempts - current_fails
            verification_result.reason += f" [Attempt {current_fails}/{self.max_allowed_failed_attempts} failed. {remaining} attempt(s) remaining before Freeze Mode]."
            print(f"[RECLAIM SYSTEM] BLOCK - Authorization failed ({current_fails}/{self.max_allowed_failed_attempts} attempts). {remaining} attempt(s) remaining.")

        return verification_result
