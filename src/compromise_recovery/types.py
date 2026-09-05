from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    RECOVERY_PENDING = "RECOVERY_PENDING"
    CONTAINMENT_LOCKED = "CONTAINMENT_LOCKED"


class FreezeReason(str, Enum):
    MAX_HARDWARE_FAILS_EXCEEDED = "MAX_HARDWARE_FAILS_EXCEEDED"
    REPLAY_ATTACK_DETECTED = "REPLAY_ATTACK_DETECTED"
    UNAUTHORIZED_BIOMETRIC = "UNAUTHORIZED_BIOMETRIC"
    MANUAL_EMERGENCY_FREEZE = "MANUAL_EMERGENCY_FREEZE"
    SUSPICIOUS_RESERVE_ACCESS = "SUSPICIOUS_RESERVE_ACCESS"


@dataclass
class FreezeEvent:
    event_id: str
    user_id: str
    reason: FreezeReason
    timestamp: str
    associated_tx_id: Optional[str] = None
    risk_factors: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmergencyNotification:
    notification_id: str
    user_id: str
    channel: str  # SMS / EMAIL
    recipient_contact: str
    title: str
    message: str
    recovery_token: str
    otp_code: str
    timestamp: str


@dataclass
class RecoveryRequest:
    user_id: str
    recovery_token: str
    otp_code: str
    hardware_public_key: Optional[str] = None
    hardware_challenge_signature: Optional[str] = None


@dataclass
class RecoveryResult:
    success: bool
    user_id: str
    status: AccountStatus
    message: str
    restored_at: Optional[str] = None
    error: Optional[str] = None
