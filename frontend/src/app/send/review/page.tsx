"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import {
  beneficiaries,
  INITIAL_OPERATIONAL_FUNDS,
  PROTECTED_RESERVE,
} from "@/data/mockData";
import { handoffToRiskEngine } from "@/lib/riskEngineHandoff";
import { TransactionPayload } from "@/types/transaction";
import "./review.css";

function ReviewContent() {
  const searchParams = useSearchParams();

  const [isChecking, setIsChecking] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);

  const beneficiaryIdParam = searchParams.get("beneficiaryId");
  const amountParam = searchParams.get("amount");
  const noteParam = searchParams.get("note") || "";

  const beneficiary =
    beneficiaries.find((b) => String(b.id) === beneficiaryIdParam) ||
    beneficiaries[0];

  const numericAmount = Number(amountParam) > 0 ? Number(amountParam) : 2000;
  const noteText = noteParam.trim();

  const remainingOperationalFunds = Math.max(
    0,
    INITIAL_OPERATIONAL_FUNDS - numericAmount
  );

  const handleConfirmAndSend = async () => {
    if (isChecking || isConfirmed) return;

    setIsChecking(true);

    const transactionId = `TXN-${Date.now().toString(36).toUpperCase()}-${Math.random()
      .toString(36)
      .substring(2, 7)
      .toUpperCase()}`;
    const timestamp = new Date().toISOString();

    const transaction: TransactionPayload = {
      amount: numericAmount,
      recipient: beneficiary.name,
      recipientAccount: beneficiary.account,
      note: noteText,
      timestamp,
      transactionId,
    };

    try {
      await new Promise((resolve) => setTimeout(resolve, 600));
      await handoffToRiskEngine(transaction);
      setIsConfirmed(true);
    } catch (error) {
      console.error("Risk engine handoff failed:", error);
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <main className="review-page">
      <div className="review-container">
        <header className="review-header">
          <Link href="/send" className="back-button" aria-label="Back to Send">
            ←
          </Link>
          <h1>Review Transaction</h1>
          <div className="header-spacer" />
        </header>

        <section className="amount-hero">
          <p className="amount-hero-label">Transfer Amount</p>
          <div className="amount-hero-value">
            ₹{numericAmount.toLocaleString("en-IN")}
          </div>
        </section>

        <section className="review-section">
          <div className="details-card">
            <div className="card-row">
              <span className="row-label">Recipient</span>
              <div className="recipient-cluster">
                <div className="recipient-avatar-small">
                  {beneficiary.initials}
                </div>
                <span className="row-value">{beneficiary.name}</span>
              </div>
            </div>

            <div className="card-row">
              <span className="row-label">Account Number</span>
              <span className="row-value account-badge">
                {beneficiary.account}
              </span>
            </div>

            <div className="card-row">
              <span className="row-label">Source Account</span>
              <span className="row-value">
                <span className="funds-tag">Operational Funds</span>
              </span>
            </div>

            {noteText ? (
              <div className="card-row">
                <span className="row-label">Note</span>
                <span className="row-value">{noteText}</span>
              </div>
            ) : null}
          </div>
        </section>

        <section className="review-section">
          <div className="balance-breakdown-card">
            <div className="breakdown-row">
              <span>Current Operational Funds</span>
              <span>₹{INITIAL_OPERATIONAL_FUNDS.toLocaleString("en-IN")}</span>
            </div>

            <div className="breakdown-row deduction">
              <span>Transfer Amount</span>
              <span>-₹{numericAmount.toLocaleString("en-IN")}</span>
            </div>

            <div className="breakdown-divider" />

            <div className="breakdown-row highlight">
              <span>Remaining Operational Funds</span>
              <span>₹{remainingOperationalFunds.toLocaleString("en-IN")}</span>
            </div>
          </div>
        </section>

        <div className="review-bottom-action">
          <button
            className="confirm-button"
            onClick={handleConfirmAndSend}
            disabled={isChecking || isConfirmed}
          >
            {isChecking
              ? "Checking..."
              : isConfirmed
              ? "Confirmed"
              : "Confirm & Send"}
          </button>

          <Link href="/send" className="cancel-button">
            Cancel
          </Link>
        </div>
      </div>
    </main>
  );
}

export default function ReviewPage() {
  return (
    <Suspense
      fallback={
        <div className="review-page">
          <div className="review-container">
            <div className="review-loading">Loading transaction review...</div>
          </div>
        </div>
      }
    >
      <ReviewContent />
    </Suspense>
  );
}
