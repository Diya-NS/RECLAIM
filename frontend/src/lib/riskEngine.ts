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
