import { Beneficiary, TransactionRecord } from "@/types/transaction";

export const beneficiaries: Beneficiary[] = [
  {
    id: 1,
    name: "Rahul",
    account: "•••• 4821",
    initials: "R",
  },
  {
    id: 2,
    name: "Ananya",
    account: "•••• 1937",
    initials: "A",
  },
  {
    id: 3,
    name: "Arjun",
    account: "•••• 7264",
    initials: "A",
  },
];

export const TOTAL_BALANCE = 200000;
export const INITIAL_OPERATIONAL_FUNDS = 20000;
export const PROTECTED_RESERVE = 180000;

export const mockTransactions: TransactionRecord[] = [
  {
    id: "tx-1",
    name: "Rahul",
    type: "Sent",
    amount: -2000,
    date: "Today, 10:42 AM",
    status: "Completed",
    account: "•••• 4821",
    note: "Lunch split",
  },
  {
    id: "tx-2",
    name: "Swiggy",
    type: "Payment",
    amount: -450,
    date: "Today, 9:18 AM",
    status: "Completed",
    account: "Merchant UPI",
    note: "Breakfast order",
  },
  {
    id: "tx-3",
    name: "Salary",
    type: "Received",
    amount: 45000,
    date: "Yesterday",
    status: "Completed",
    account: "Acme Corp Payroll",
    note: "Monthly compensation",
  },
  {
    id: "tx-4",
    name: "Ananya",
    type: "Sent",
    amount: -1200,
    date: "Sep 2, 2026",
    status: "Completed",
    account: "•••• 1937",
    note: "Concert tickets",
  },
  {
    id: "tx-5",
    name: "Client Payout",
    type: "Received",
    amount: 12500,
    date: "Aug 29, 2026",
    status: "Completed",
    account: "Direct Deposit",
    note: "Freelance project payment",
  },
  {
    id: "tx-6",
    name: "Arjun",
    type: "Sent",
    amount: -800,
    date: "Aug 25, 2026",
    status: "Completed",
    account: "•••• 7264",
    note: "Grocery contribution",
  },
];

