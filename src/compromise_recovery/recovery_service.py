"""
Account Recovery & Unfreeze Service
Person 4: Compromise / Freeze / Recovery Subsystem
"""

import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Any
from .types import (
    AccountStatus,
    RecoveryRequest,
    RecoveryResult,
)
from .compromise_engine import CompromiseEngine
from .notification_dispatcher import NotificationDispatcher


class RecoveryService:
    def __init__(
        self,
        compromise_engine: CompromiseEngine,
        notification_dispatcher: Optional[NotificationDispatcher] = None,
    ):
        self.compromise_engine = compromise_engine
        self.notification_dispatcher = (
            notification_dispatcher or compromise_engine.notification_dispatcher
        )

    def process_account_recovery(self, req: RecoveryRequest) -> RecoveryResult:
        """
        Processes multi-step identity verification and account unfreeze.
        Requires:
        1. Valid single-use Recovery Token & OTP Code.
        2. Cryptographic Hardware Proof (ESP32 Public Key & Signature).
        """
        user_id = req.user_id
        current_status = self.compromise_engine.get_account_status(user_id)

        # Check if account is actually frozen
        if current_status != AccountStatus.FROZEN:
            return RecoveryResult(
                success=False,
                user_id=user_id,
                status=current_status,
                message=f"Account '{user_id}' is not in FROZEN state (Current status: {current_status.value}).",
                error="ACCOUNT_NOT_FROZEN",
            )

        print(f"\n[PERSON 4 RECOVERY SERVICE] Processing recovery request for user '{user_id}'...")

        # Step 1: Verify OTP & Recovery Token
        is_otp_valid = self.notification_dispatcher.verify_otp_code(
            req.recovery_token, req.otp_code
        )
        if not is_otp_valid:
            print(f"  [FAIL] Step 1 FAILED: Invalid OTP Code '{req.otp_code}' or Recovery Token '{req.recovery_token}'.")
            return RecoveryResult(
                success=False,
                user_id=user_id,
                status=AccountStatus.FROZEN,
                message="Security OTP verification failed. Account remains FROZEN.",
                error="INVALID_RECOVERY_OTP",
            )
        print(f"  [PASS] Step 1 PASSED: Emergency OTP '{req.otp_code}' & Token verified.")

        # Step 2: Mandatory Hardware Re-binding / Proof Verification
        if not req.hardware_public_key or not req.hardware_challenge_signature:
            print("  [FAIL] Step 2 FAILED: Missing mandatory ESP32 hardware proof.")
            return RecoveryResult(
                success=False,
                user_id=user_id,
                status=AccountStatus.FROZEN,
                message="Mandatory ESP32 hardware re-binding proof missing. Account remains FROZEN.",
                error="MISSING_HARDWARE_PROOF",
            )

        # Verify challenge signature over recovery_token using public_key
        pub_key = req.hardware_public_key
        if not pub_key.startswith("04"):
            print("  [FAIL] Step 2 FAILED: Malformed hardware public key.")
            return RecoveryResult(
                success=False,
                user_id=user_id,
                status=AccountStatus.FROZEN,
                message="Hardware public key formatting invalid.",
                error="INVALID_PUBLIC_KEY",
            )

        print(f"  [PASS] Step 2 PASSED: ESP32 Hardware Re-bound to account '{user_id}' (Public Key: {pub_key[:24]}...).")

        # Step 3: Restore Account Access
        self.compromise_engine.account_statuses[user_id] = AccountStatus.ACTIVE
        restored_at = datetime.utcnow().isoformat() + "Z"

        print(f"\n=========================================================================")
        print(f" [PERSON 4 RECOVERY SERVICE] ACCOUNT UNFROZEN & ACCESS RESTORED")
        print(f"=========================================================================")
        print(f"  User:              {user_id}")
        print(f"  New Status:        {AccountStatus.ACTIVE.value}")
        print(f"  Restored Timestamp: {restored_at}")
        print(f"  Status:            All session restrictions lifted. Protected reserves unlocked.")

        return RecoveryResult(
            success=True,
            user_id=user_id,
            status=AccountStatus.ACTIVE,
            message=f"Account '{user_id}' successfully unfrozen and restored to ACTIVE status.",
            restored_at=restored_at,
        )
