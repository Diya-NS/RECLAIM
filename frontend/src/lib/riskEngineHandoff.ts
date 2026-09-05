import { TransactionPayload } from "@/types/transaction";

export type HandoffStatus = "HANDOFF_RECEIVED";

export async function handoffToRiskEngine(
  transaction: TransactionPayload
): Promise<HandoffStatus> {
  console.log("[RiskEngineHandoff] Payload received:", transaction);

  return "HANDOFF_RECEIVED";
}
