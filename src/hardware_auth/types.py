from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskDecision(str, Enum):
    TRIGGER_RECLAIM = "TRIGGER_RECLAIM"
    ALLOW = "ALLOW"
    DENY = "DENY"


class AuthorizationStatus(str, Enum):
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    FREEZE_MODE_TRIGGERED = "FREEZE_MODE_TRIGGERED"
    PENDING_HARDWARE_PROOF = "PENDING_HARDWARE_PROOF"
    FAILED_VERIFICATION = "FAILED_VERIFICATION"


@dataclass
class TransactionPayload:
    transaction_id: str
    amount: float
    recipient: str
    sender: str
    risk_level: RiskLevel
    risk_score: float
    timestamp: str
    nonce: str
    risk_decision: str = RiskDecision.TRIGGER_RECLAIM.value
    risk_factors: List[str] = field(default_factory=lambda: ["protected_reserve_accessed", "amount_exceeded"])
    challenge_id: str = "CHAL-9F8A2B1C"
    challenge_payload: str = "a7c3b2f901e4d812"


@dataclass
class HardwareAuthRequest:
    transaction_id: str
    amount: float
    recipient: str
    nonce: str
    timestamp: str
    challenge_id: str
    challenge_payload: str


@dataclass
class HardwareAuthResponse:
    success: bool
    transaction_id: str
    challenge_id: Optional[str] = None
    challenge_payload: Optional[str] = None
    challenge_signature: Optional[str] = None
    payload_hash: Optional[str] = None
    signature: Optional[str] = None
    public_key: Optional[str] = None
    device_id: Optional[str] = None
    biometric_verified: bool = False
    liveness_verified: bool = False
    message: str = ""
    error: Optional[str] = None


@dataclass
class VerificationResult:
    is_valid: bool
    status: AuthorizationStatus
    reason: str
    failed_attempts_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
