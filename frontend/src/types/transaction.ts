export interface Beneficiary {
  id: number;
  name: string;
  account: string;
  initials: string;
}

export interface TransactionPayload {
  amount: number;
  recipient: string;
  recipientAccount: string;
  note: string;
  timestamp: string;
  transactionId: string;
}

export interface TransactionRecord {
  id: string;
  name: string;
  type: "Sent" | "Payment" | "Received";
  amount: number;
  date: string;
  status: string;
  account?: string;
  note?: string;
}

export type RiskLevel = "LOW" | "HIGH";

export interface RiskResult {
  riskScore: number;
  riskLevel: RiskLevel;
  indicators?: string[];
}


