import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="RECLAIM Security & Risk Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---


class TransactionContext(BaseModel):
  user_id: str
  amount: float
  recipient_id: str
  device_id: str
  sim_id: Optional[str] = "sim_icc_8991004821"
  ip_address: str = "127.0.0.1"


class RiskEvaluation(BaseModel):
  risk_score: int
  decision: str  # "APPROVE", "STEP_UP_AUTH", "TRIGGER_RECLAIM"
  challenge_id: Optional[str] = None  # Transaction nonce for Person 3
  challenge_payload: Optional[str] = None  # Canonical hash for ESP32 signing
  risk_factors: List[str]
  breakdown: Dict[str, int]


# --- USER BASELINE DATA ---

USER_DATABASE = {
    "user_101": {
        "operational_limit": 20000.0,
        "protected_reserve": 180000.0,
        "known_devices": {"device_pixel8_abc", "macbook_chrome_xyz"},
        "known_recipients": {"mom_axis_001", "landlord_hdfc_002"},
        "registered_sim_id": "sim_icc_8991004821",
        "trust_score": 85,
    }
}

TRANSACTION_HISTORY: Dict[str, List[dict]] = {"user_101": []}


# --- RISK EVALUATION ENDPOINT ---


@app.post("/api/v1/risk/evaluate", response_model=RiskEvaluation)
def evaluate_transaction(txn: TransactionContext):
  user = USER_DATABASE.get(txn.user_id)
  if not user:
    raise HTTPException(status_code=404, detail="User account not found")

  risk_score = 0
  factors = []
  breakdown = {}

  # 1. Amount Risk (Max 40 pts)
  op_limit = user["operational_limit"]
  if txn.amount > op_limit:
    excess_ratio = min((txn.amount - op_limit) / op_limit, 4.0)
    amount_penalty = int(25 + (excess_ratio * 3.75))
    risk_score += amount_penalty
    factors.append(
        f"Amount ₹{txn.amount:,.2f} exceeds operational limit ₹{op_limit:,.2f}"
    )
    breakdown["amount_risk"] = amount_penalty
  elif txn.amount > (op_limit * 0.75):
    risk_score += 15
    factors.append("Amount close to operational limit")
    breakdown["amount_risk"] = 15
  else:
    breakdown["amount_risk"] = 0

  # 2. Recipient Risk (Max 25 pts)
  if txn.recipient_id not in user["known_recipients"]:
    risk_score += 25
    factors.append("New/untrusted beneficiary")
    breakdown["recipient_risk"] = 25
  else:
    breakdown["recipient_risk"] = 0

  # 3. Device Risk (Max 20 pts)
  if txn.device_id not in user["known_devices"]:
    risk_score += 20
    factors.append("Unrecognized device fingerprint")
    breakdown["device_risk"] = 20
  else:
    breakdown["device_risk"] = 0

  # 4. SIM Binding Risk (Max 40 pts) - Device hardware SIM verification
  reg_sim = user.get("registered_sim_id")
  if not txn.sim_id or (reg_sim and txn.sim_id != reg_sim):
    risk_score += 40
    factors.append(
        f"SIM Binding Mismatch: Active SIM '{txn.sim_id}' does not match"
        f" registered SIM '{reg_sim}'"
    )
    breakdown["sim_risk"] = 40
  else:
    breakdown["sim_risk"] = 0

  # 4. Velocity Risk (Max 15 pts) - Rapid drain detection
  now = datetime.utcnow()
  ten_mins_ago = now - timedelta(minutes=10)
  recent_txns = [
      t
      for t in TRANSACTION_HISTORY.get(txn.user_id, [])
      if t["timestamp"] > ten_mins_ago
  ]

  if len(recent_txns) >= 3:
    risk_score += 15
    factors.append(f"Velocity spike: {len(recent_txns)} transactions in 10 mins")
    breakdown["velocity_risk"] = 15
  elif len(recent_txns) >= 1:
    risk_score += 5
    breakdown["velocity_risk"] = 5
  else:
    breakdown["velocity_risk"] = 0

  # 5. Cumulative Volume (Max 15 pts) - Smurfing detection
  recent_total = sum(t["amount"] for t in recent_txns) + txn.amount
  if recent_total > op_limit and txn.amount <= op_limit:
    risk_score += 15
    factors.append(
        f"Cumulative session total (₹{recent_total:,.2f}) breaks operational"
        " boundary"
    )
    breakdown["cumulative_risk"] = 15
  else:
    breakdown["cumulative_risk"] = 0

  # Clamp score between 0 and 100
  final_score = min(max(risk_score, 0), 100)

  # Decision Matrix & Challenge Generation
  challenge_id = None
  challenge_payload = None

  if final_score >= 70 or txn.amount >= (op_limit * 2):
    decision = "TRIGGER_RECLAIM"
    challenge_id = f"CHAL-{uuid.uuid4().hex[:8].upper()}"

    # SHA256 digest string for ESP32 display and hardware key signing
    raw_str = f"{txn.user_id}:{txn.recipient_id}:{txn.amount}:{now.isoformat()}"
    challenge_payload = hashlib.sha256(raw_str.encode()).hexdigest()[:16]
  elif final_score >= 40:
    decision = "STEP_UP_AUTH"
  else:
    decision = "APPROVE"

  # Log into transaction history
  TRANSACTION_HISTORY.setdefault(txn.user_id, []).append({
      "amount": txn.amount,
      "recipient_id": txn.recipient_id,
      "device_id": txn.device_id,
      "timestamp": now,
  })

  return RiskEvaluation(
      risk_score=final_score,
      decision=decision,
      challenge_id=challenge_id,
      challenge_payload=challenge_payload,
      risk_factors=factors,
      breakdown=breakdown,
  )


# --- ACCOUNT STATUS ENDPOINT (For Person 4) ---


@app.get("/api/v1/risk/status/{user_id}")
def get_user_status(user_id: str):
  user = USER_DATABASE.get(user_id)
  if not user:
    raise HTTPException(status_code=404, detail="User not found")
  return {
      "user_id": user_id,
      "trust_score": user["trust_score"],
      "operational_limit": user["operational_limit"],
      "protected_reserve": user["protected_reserve"],
      "status": "SECURE",
  }


# --- PERSON 3 HARDWARE AUTHORIZATION BRIDGE ---

import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
  sys.path.insert(0, ROOT_DIR)

from src.hardware_auth import (
    RiskLevel,
    RiskDecision,
    TransactionPayload,
    HardwareClient,
    SignatureVerifier,
    HardwareAuthorizationService,
    AuthorizationStatus,
)

HARDWARE_URL = os.getenv("RECLAIM_HARDWARE_URL", "http://127.0.0.1:8585")
hardware_client = HardwareClient(endpoint_url=HARDWARE_URL)
signature_verifier = SignatureVerifier()


def on_person4_freeze_alert(tx: TransactionPayload, ver_res):
  print(
      f"\n[PERSON 4 ALERT - FREEZE TRIGGERED] User '{tx.sender}' frozen due to"
      " 3 failed attempts!"
  )
  user = USER_DATABASE.get(tx.sender)
  if user:
    user["status"] = "FROZEN"


hardware_service = HardwareAuthorizationService(
    hardware_client=hardware_client,
    signature_verifier=signature_verifier,
    person4_compromise_handler=on_person4_freeze_alert,
    max_allowed_failed_attempts=3,
)


class HardwareAuthorizeRequest(BaseModel):
  transaction_id: str
  amount: float
  recipient: str
  sender: str = "user_101"
  risk_level: str = "CRITICAL"
  risk_score: float = 0.75
  timestamp: Optional[str] = None
  nonce: Optional[str] = None
  risk_decision: str = "TRIGGER_RECLAIM"
  risk_factors: List[str] = []
  challenge_id: str
  challenge_payload: str


class HardwareAuthorizeResponse(BaseModel):
  is_valid: bool
  status: str
  reason: str
  failed_attempts_count: int = 0
  details: Dict[str, Any] = {}
  error: Optional[str] = None


@app.get("/api/v1/hardware/status")
def get_hardware_status():
  return hardware_client.get_device_status()


@app.post(
    "/api/v1/hardware/authorize", response_model=HardwareAuthorizeResponse
)
def authorize_hardware_transaction(req: HardwareAuthorizeRequest):
  # 1. Verify hardware device connectivity
  dev_status = hardware_client.get_device_status()
  if dev_status.get("online") is False:
    return HardwareAuthorizeResponse(
        is_valid=False,
        status="UNAVAILABLE",
        reason="Security authorization unavailable. Please try again.",
        failed_attempts_count=hardware_service.get_failed_attempts(req.sender),
        error=dev_status.get("error", "Hardware device unreachable"),
        details={"step": "HARDWARE_CONNECTIVITY"},
    )

  # Auto-register device public key if known
  pubkey = dev_status.get("public_key")
  if pubkey and pubkey not in signature_verifier.allowed_public_keys:
    signature_verifier.register_trusted_device_key(pubkey)

  # 2. Build TransactionPayload using Person 3's exact domain model
  risk_level_enum = RiskLevel.CRITICAL
  if req.risk_level in RiskLevel.__members__:
    risk_level_enum = RiskLevel(req.risk_level)

  tx = TransactionPayload(
      transaction_id=req.transaction_id,
      amount=req.amount,
      recipient=req.recipient,
      sender=req.sender,
      risk_level=risk_level_enum,
      risk_score=req.risk_score,
      timestamp=req.timestamp or datetime.utcnow().isoformat(),
      nonce=req.nonce or f"nonce_{uuid.uuid4().hex[:12]}",
      risk_decision=req.risk_decision,
      risk_factors=req.risk_factors or ["protected_reserve_accessed"],
      challenge_id=req.challenge_id,
      challenge_payload=req.challenge_payload,
  )

  # 3. Process authorization via Person 3's HardwareAuthorizationService
  res = hardware_service.process_transaction_authorization(tx)

  return HardwareAuthorizeResponse(
      is_valid=res.is_valid,
      status=(
          res.status.value if hasattr(res.status, "value") else str(res.status)
      ),
      reason=res.reason,
      failed_attempts_count=res.failed_attempts_count,
      details=res.details,
  )


@app.post("/api/v1/hardware/reset")
def reset_hardware_state():
  hardware_service.reset_failed_attempts("user_101")
  user = USER_DATABASE.get("user_101")
  if user:
    user["status"] = "SECURE"
  signature_verifier.used_nonces.clear()
  return {
      "status": "RESET",
      "user_id": "user_101",
      "user_status": "SECURE",
      "failed_attempts": hardware_service.get_failed_attempts("user_101"),
  }


