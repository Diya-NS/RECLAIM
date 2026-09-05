"""
Emergency Security Notification Dispatcher
Person 4: Compromise / Freeze / Recovery Subsystem
"""

import uuid
import random
from typing import List, Dict, Any, Tuple
from .types import EmergencyNotification, FreezeEvent


class NotificationDispatcher:
    def __init__(self):
        # Store dispatched notifications in memory for verification
        self.dispatched_notifications: List[EmergencyNotification] = []
        self.active_recovery_otps: Dict[str, Tuple[str, str]] = {}  # token -> (user_id, otp_code)

    def generate_otp(self) -> str:
        return f"{random.randint(100000, 999999)}"

    def dispatch_freeze_alert(
        self, freeze_event: FreezeEvent, user_email: str, user_phone: str
    ) -> Tuple[EmergencyNotification, EmergencyNotification]:
        """
        Dispatches emergency security alerts via SMS and Email channels.
        """
        recovery_token = f"REC-TOKEN-{uuid.uuid4().hex[:12].upper()}"
        otp_code = self.generate_otp()

        # Store active recovery OTP associated with recovery_token
        self.active_recovery_otps[recovery_token] = (freeze_event.user_id, otp_code)

        email_notif = EmergencyNotification(
            notification_id=f"NOTIF-EMAIL-{uuid.uuid4().hex[:8]}",
            user_id=freeze_event.user_id,
            channel="EMAIL",
            recipient_contact=user_email,
            title="SECURITY ALERT: Account Frozen Due to Failed Authorization",
            message=(
                f"ALERT: Your RECLAIM account '{freeze_event.user_id}' has been temporarily FROZEN.\n"
                f"Reason: {freeze_event.reason.value} (Tx ID: {freeze_event.associated_tx_id or 'N/A'}).\n"
                f"All pending transactions and Protected Reserve withdrawals have been locked.\n\n"
                f"To unfreeze your account, use your Recovery Code: {otp_code} and Recovery Token: {recovery_token}."
            ),
            recovery_token=recovery_token,
            otp_code=otp_code,
            timestamp=freeze_event.timestamp,
        )

        sms_notif = EmergencyNotification(
            notification_id=f"NOTIF-SMS-{uuid.uuid4().hex[:8]}",
            user_id=freeze_event.user_id,
            channel="SMS",
            recipient_contact=user_phone,
            title="SECURITY ALERT",
            message=(
                f"RECLAIM ALERT: Account '{freeze_event.user_id}' FROZEN. "
                f"Security OTP: {otp_code}. Token: {recovery_token}"
            ),
            recovery_token=recovery_token,
            otp_code=otp_code,
            timestamp=freeze_event.timestamp,
        )

        self.dispatched_notifications.extend([email_notif, sms_notif])

        print(f"\n[PERSON 4 DISPATCHER] Emergency Security Alerts Dispatched!")
        print(f"  |- EMAIL -> {user_email}: '{email_notif.title}'")
        print(f"  |- SMS   -> {user_phone}: OTP={otp_code} | Token={recovery_token}")

        return email_notif, sms_notif

    def verify_otp_code(self, recovery_token: str, otp_code: str) -> bool:
        if recovery_token not in self.active_recovery_otps:
            return False
        stored_user, stored_otp = self.active_recovery_otps[recovery_token]
        return stored_otp == otp_code
