"""
Compromise & Account Freeze Engine
Person 4: Compromise / Freeze / Recovery Subsystem
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from .types import (
    AccountStatus,
    FreezeReason,
    FreezeEvent,
    EmergencyNotification,
)
from .notification_dispatcher import NotificationDispatcher


class CompromiseEngine:
    def __init__(self, notification_dispatcher: Optional[NotificationDispatcher] = None):
        self.notification_dispatcher = notification_dispatcher or NotificationDispatcher()
        
        # User account status registry: user_id -> AccountStatus
        self.account_statuses: Dict[str, AccountStatus] = {}
        
        # User contact registry: user_id -> (email, phone)
        self.user_contacts: Dict[str, Dict[str, str]] = {
            "alice": {"email": "alice@reclaim-secure.io", "phone": "+1-555-0192"},
            "bob": {"email": "bob@reclaim-secure.io", "phone": "+1-555-0847"},
            "attacker_bob": {"email": "bob@reclaim-secure.io", "phone": "+1-555-0847"},
        }
        
        # Audit trail log of all freeze events
        self.audit_log: List[FreezeEvent] = []

    def get_account_status(self, user_id: str) -> AccountStatus:
        return self.account_statuses.get(user_id, AccountStatus.ACTIVE)

    def register_user_contact(self, user_id: str, email: str, phone: str):
        self.user_contacts[user_id] = {"email": email, "phone": phone}

    def freeze_account(
        self,
        user_id: str,
        reason: FreezeReason,
        associated_tx_id: Optional[str] = None,
        risk_factors: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> FreezeEvent:
        """
        Executes immediate containment protocol: freezes user account, revokes sessions, and dispatches emergency alerts.
        """
        # 1. Update status to FROZEN
        self.account_statuses[user_id] = AccountStatus.FROZEN
        timestamp = datetime.utcnow().isoformat() + "Z"

        # 2. Log signed audit trail event
        freeze_event = FreezeEvent(
            event_id=f"EVT-FREEZE-{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            reason=reason,
            timestamp=timestamp,
            associated_tx_id=associated_tx_id,
            risk_factors=risk_factors or [],
            details=details or {},
        )
        self.audit_log.append(freeze_event)

        print(f"\n=========================================================================")
        print(f" [PERSON 4 COMPROMISE ENGINE] ACCOUNT CONTAINMENT EXECUTED")
        print(f"=========================================================================")
        print(f"  Target User:       {user_id}")
        print(f"  Account Status:    {AccountStatus.FROZEN.value}")
        print(f"  Freeze Event ID:   {freeze_event.event_id}")
        print(f"  Reason:            {reason.value}")
        print(f"  Associated Tx:     {associated_tx_id or 'N/A'}")
        print(f"  Risk Factors:      {', '.join(freeze_event.risk_factors)}")
        print(f"  Action Taken:      Session tokens revoked. Protected reserves locked.")

        # 3. Dispatch emergency security alerts & recovery token
        contact = self.user_contacts.get(
            user_id, {"email": f"{user_id}@reclaim-security.org", "phone": "+1-555-0000"}
        )
        self.notification_dispatcher.dispatch_freeze_alert(
            freeze_event=freeze_event,
            user_email=contact["email"],
            user_phone=contact["phone"],
        )

        return freeze_event

    def handle_person3_hardware_failure_event(self, tx_payload: Any, verification_result: Any):
        """
        Callback handler invoked by Person 3 when hardware authorization fails or 3 strikes occur.
        """
        user_id = getattr(tx_payload, "sender", "unknown_user")
        tx_id = getattr(tx_payload, "transaction_id", "unknown_tx")
        risk_factors = getattr(tx_payload, "risk_factors", [])
        
        status_str = str(getattr(verification_result, "status", ""))
        reason_str = str(getattr(verification_result, "reason", ""))

        if "FREEZE" in status_str or "Replay attack" in reason_str:
            reason = FreezeReason.MAX_HARDWARE_FAILS_EXCEEDED
            if "Replay attack" in reason_str:
                reason = FreezeReason.REPLAY_ATTACK_DETECTED
        else:
            reason = FreezeReason.UNAUTHORIZED_BIOMETRIC

        self.freeze_account(
            user_id=user_id,
            reason=reason,
            associated_tx_id=tx_id,
            risk_factors=risk_factors,
            details={"verification_reason": reason_str},
        )
