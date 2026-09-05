"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import "./verify.css";

function VerifyContent() {
  const searchParams = useSearchParams();

  const amountParam = searchParams.get("amount");
  const recipientParam = searchParams.get("recipient") || "Beneficiary";
  const recipientAccountParam = searchParams.get("recipientAccount") || "";
  const decision = searchParams.get("decision") || "APPROVE";
  const riskScore = searchParams.get("risk_score") || "0";

  const numericAmount = Number(amountParam) > 0 ? Number(amountParam) : 2000;
  const formattedAmount = `₹${numericAmount.toLocaleString("en-IN")}`;

  const isApproved = decision === "APPROVE";
  const isStepUp = decision === "STEP_UP_AUTH";
  const isReclaim = decision === "TRIGGER_RECLAIM";

  return (
    <main className="verify-page">
      <div className="verify-container">
        <header className="verify-header">
          <Link href="/send/risk" className="back-button" aria-label="Back">
            ←
          </Link>
          <h1>
            {isApproved
              ? "Authorization"
              : isStepUp
              ? "Verification"
              : "Protection"}
          </h1>
          <div className="header-spacer" />
        </header>

        <section className="verify-hero">
          <div
            className={`verify-badge ${
              isApproved ? "approve" : isStepUp ? "step_up" : "reclaim"
            }`}
          >

          </div>

          <h2 className="verify-title">
            {isApproved && "Transaction Authorization"}
            {isStepUp && "Enhanced Verification Required"}
            {isReclaim && "RECLAIM Security Protocol"}
          </h2>

          <p className="verify-subtitle">
            {isApproved &&
              "Your transaction passed security evaluation. Final authorization will be performed here."}
            {isStepUp &&
              "Elevated factors were detected. Step-up authorization will be performed here."}
            {isReclaim &&
              "Operational threshold exceeded. Security authorization protocol is required before release."}
          </p>
        </section>

        <section className="verify-card">
          <div className="verify-row">
            <span className="verify-label">Transfer Amount</span>
            <span className="verify-amount">{formattedAmount}</span>
          </div>

          <div className="verify-divider" />

          <div className="verify-row">
            <span className="verify-label">Recipient</span>
            <span className="verify-name">{recipientParam}</span>
            {recipientAccountParam && (
              <span className="verify-account">{recipientAccountParam}</span>
            )}
          </div>

          <div className="verify-divider" />

          <div className="verify-row">
            <span className="verify-label">Security Score</span>
            <span className="verify-status">{riskScore} / 100</span>
          </div>
        </section>

        <section className="notice-box">
          <div className="notice-icon">🛡️</div>
          <div className="notice-content">
            <strong>Security Milestone Reached</strong>
            <p>
              Evaluation complete. Next-stage authorization protocols will activate in the
              subsequent security phase. No funds have been transferred.
            </p>
          </div>
        </section>

        <div className="verify-spacer" />

        <div className="verify-actions">
          <Link href="/dashboard" className="verify-primary-button">
            Return to Dashboard
          </Link>
          <Link href="/send" className="verify-secondary-button">
            New Transfer
          </Link>
        </div>
      </div>
    </main>
  );
}

export default function VerifyPage() {
  return (
    <Suspense
      fallback={
        <div className="verify-page">
          <div className="verify-container">
            <div className="verify-loading">Loading authorization status...</div>
          </div>
        </div>
      }
    >
      <VerifyContent />
    </Suspense>
  );
}
