import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
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
