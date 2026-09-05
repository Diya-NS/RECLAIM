export type RiskDecision = "APPROVE" | "STEP_UP_AUTH" | "TRIGGER_RECLAIM";

export interface RiskEvaluationRequest {
  user_id: string;
  amount: number;
  recipient_id: string;
  device_id: string;
  ip_address: string;
}

export interface RiskEvaluationResponse {
  risk_score: number;
  decision: RiskDecision;
  risk_factors: string[];
  breakdown: Record<string, number>;
  challenge_id?: string | null;
  challenge_payload?: string | null;
}

export interface EvaluateTransactionParams {
  amount: number;
  recipientId: string | number;
  userId?: string;
  deviceId?: string;
  ipAddress?: string;
}

const DEFAULT_BASE_URL = "http://localhost:8000";

export async function evaluateTransaction(
  params: EvaluateTransactionParams
): Promise<RiskEvaluationResponse> {
  const baseUrl =
    process.env.NEXT_PUBLIC_RISK_ENGINE_URL || DEFAULT_BASE_URL;

  const payload: RiskEvaluationRequest = {
    user_id: params.userId || "user_101",
    amount: params.amount,
    recipient_id: String(params.recipientId),
    device_id: params.deviceId || "device_pixel8_abc",
    ip_address: params.ipAddress || "127.0.0.1",
  };

  const response = await fetch(`${baseUrl}/api/v1/risk/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "");
    throw new Error(
      `Transaction check failed with status ${response.status}: ${errorText}`
    );
  }

  const data: RiskEvaluationResponse = await response.json();
  return data;
}

// --- PERSON 3 HARDWARE AUTHORIZATION CLIENT ---

export interface HardwareAuthorizeRequest {
  transaction_id: string;
  amount: number;
  recipient: string;
  sender?: string;
  risk_level?: string;
  risk_score?: number;
  timestamp?: string;
  nonce?: string;
  risk_decision?: string;
  risk_factors?: string[];
  challenge_id: string;
  challenge_payload: string;
}

export type HardwareAuthStatus =
  | "APPROVED"
  | "BLOCKED"
  | "FREEZE_MODE_TRIGGERED"
  | "UNAVAILABLE";

export interface HardwareAuthorizeResponse {
  is_valid: boolean;
  status: HardwareAuthStatus;
  reason: string;
  failed_attempts_count: number;
  details?: Record<string, any>;
  error?: string | null;
}

export async function authorizeHardwareTransaction(
  payload: HardwareAuthorizeRequest
): Promise<HardwareAuthorizeResponse> {
  const baseUrl =
    process.env.NEXT_PUBLIC_RISK_ENGINE_URL || DEFAULT_BASE_URL;

  const response = await fetch(`${baseUrl}/api/v1/hardware/authorize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "");
    throw new Error(
      `Hardware authorization failed with status ${response.status}: ${errorText}`
    );
  }

  const data: HardwareAuthorizeResponse = await response.json();
  return data;
}
