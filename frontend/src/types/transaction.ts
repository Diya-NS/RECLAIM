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
