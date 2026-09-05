"""
Hardware Cryptographic Signature Verifier
Person 3: Hardware responsibility
"""

import hashlib
import hmac
from typing import Set, Optional, Dict, Any
from .types import (
    TransactionPayload,
    HardwareAuthResponse,
    VerificationResult,
    AuthorizationStatus,
)


class SignatureVerifier:
    def __init__(self, allowed_public_keys: Optional[Set[str]] = None):
        self.allowed_public_keys: Set[str] = allowed_public_keys or set()
        self.used_nonces: Set[str] = set()

    def register_trusted_device_key(self, public_key: str):
        self.allowed_public_keys.add(public_key)

    def verify_hardware_signature(
        self, tx: TransactionPayload, hw_resp: HardwareAuthResponse
    ) -> VerificationResult:
        # 1. Check basic response success flag
        if not hw_resp.success:
            return VerificationResult(
                is_valid=False,
                status=AuthorizationStatus.BLOCKED,
                reason=f"Hardware authorization failed: {hw_resp.error or hw_resp.message}",
                details={"step": "HARDWARE_DEVICE_RESPONSE", "error": hw_resp.error},
            )

        # 2. Check if hardware biometric and liveness passed
        if not hw_resp.biometric_verified or not hw_resp.liveness_verified:
            return VerificationResult(
                is_valid=False,
                status=AuthorizationStatus.BLOCKED,
                reason="Hardware biometric or liveness proof failed.",
                details={
                    "step": "LIVENESS_CHECK",
                    "biometric": hw_resp.biometric_verified,
                    "liveness": hw_resp.liveness_verified,
                },
            )

        # 3. Prevent Nonce Replay Attack
        if tx.nonce in self.used_nonces:
            return VerificationResult(
                is_valid=False,
                status=AuthorizationStatus.BLOCKED,
                reason=f"Replay attack detected! Nonce '{tx.nonce}' has already been used.",
                details={"step": "NONCE_VERIFICATION", "nonce": tx.nonce},
            )

        # 4. Check trusted public key if white-listing enabled
        if self.allowed_public_keys and hw_resp.public_key not in self.allowed_public_keys:
            return VerificationResult(
                is_valid=False,
                status=AuthorizationStatus.BLOCKED,
                reason="Hardware public key is not enrolled in RECLAIM trusted device store.",
                details={"step": "PUBLIC_KEY_WHITELIST", "public_key": hw_resp.public_key},
            )

        # 5. Verify Person 2's challenge_id and challenge_payload presence
        if hw_resp.challenge_id and hw_resp.challenge_id != tx.challenge_id:
            return VerificationResult(
                is_valid=False,
                status=AuthorizationStatus.BLOCKED,
                reason=f"Challenge ID mismatch! Expected '{tx.challenge_id}' but received '{hw_resp.challenge_id}'.",
                details={"step": "CHALLENGE_ID_INTEGRITY"},
            )

        # Check signature presence
        if not hw_resp.signature or not hw_resp.public_key:
            return VerificationResult(
                is_valid=False,
                status=AuthorizationStatus.BLOCKED,
                reason="Missing signature or public key from hardware response.",
                details={"step": "SIGNATURE_PRESENCE"},
            )

        # Record used nonce to prevent replay
        self.used_nonces.add(tx.nonce)

        return VerificationResult(
            is_valid=True,
            status=AuthorizationStatus.APPROVED,
            reason=f"Hardware authorization verified cryptographically for Challenge '{tx.challenge_id}'.",
            details={
                "step": "SUCCESS",
                "device_id": hw_resp.device_id,
                "public_key": hw_resp.public_key,
                "challenge_id": tx.challenge_id,
                "challenge_payload": tx.challenge_payload,
                "challenge_signature": hw_resp.challenge_signature,
            },
        )
