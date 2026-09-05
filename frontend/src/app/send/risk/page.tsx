"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import {
  INITIAL_OPERATIONAL_FUNDS,
  PROTECTED_RESERVE,
} from "@/data/mockData";
import { RiskDecision } from "@/lib/riskEngine";
import "./risk.css";

function RiskContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const amountParam = searchParams.get("amount");
  const recipientParam = searchParams.get("recipient") || "Rahul";
  const recipientAccountParam =
    searchParams.get("recipientAccount") || "•••• 4821";
  const beneficiaryIdParam = searchParams.get("beneficiaryId") || "1";
  const transactionIdParam = searchParams.get("transactionId") || "";
  const timestampParam = searchParams.get("timestamp") || "";
  const noteParam = searchParams.get("note") || "";

  // Real Risk Evaluation response parameters
  const riskScoreParam = searchParams.get("risk_score");
  const decisionParam = searchParams.get("decision") as RiskDecision | null;
  const riskFactorsParam = searchParams.get("risk_factors");
  const challengeIdParam = searchParams.get("challenge_id");
  const challengePayloadParam = searchParams.get("challenge_payload");

  const numericAmount = Number(amountParam) > 0 ? Number(amountParam) : 2000;
  const formattedAmount = `₹${numericAmount.toLocaleString("en-IN")}`;

  const hasValidRiskData =
    riskScoreParam !== null &&
    decisionParam !== null &&
    ["APPROVE", "STEP_UP_AUTH", "TRIGGER_RECLAIM"].includes(decisionParam);

  const riskScore = hasValidRiskData ? Number(riskScoreParam) : 0;
  const decision: RiskDecision = hasValidRiskData
    ? (decisionParam as RiskDecision)
    : "APPROVE";

  let riskFactors: string[] = [];
  if (riskFactorsParam) {
    try {
      riskFactors = JSON.parse(riskFactorsParam);
    } catch {
      riskFactors = [];
    }
  }

  const forwardParams = new URLSearchParams({
    amount: String(numericAmount),
    recipient: recipientParam,
    recipientAccount: recipientAccountParam,
    beneficiaryId: beneficiaryIdParam,
    decision,
    risk_score: String(riskScore),
    ...(transactionIdParam ? { transactionId: transactionIdParam } : {}),
    ...(timestampParam ? { timestamp: timestampParam } : {}),
    ...(noteParam ? { note: noteParam } : {}),
    ...(challengeIdParam ? { challenge_id: challengeIdParam } : {}),
    ...(challengePayloadParam ? { challenge_payload: challengePayloadParam } : {}),
    ...(riskFactors.length ? { risk_factors: JSON.stringify(riskFactors) } : {}),
  });

  const handleContinue = () => {
    router.push(`/send/verify?${forwardParams.toString()}`);
  };

  if (!hasValidRiskData) {
    return (
      <main className="risk-page">
        <div className="risk-container">
          <header className="risk-top-header">
            <Link href="/send" className="back-button" aria-label="Back">
              ←
            </Link>
            <h1>Security Review</h1>
            <div className="header-spacer" />
          </header>

          <section className="risk-hero-section">
            <h2 className="risk-title">Transaction check unavailable. Please try again.</h2>
            <p className="risk-subtitle">
              We could not verify the security status for this transfer.
            </p>
          </section>

          <div className="risk-bottom-action">
            <button
              className="primary-action-button"
              onClick={() => router.push("/send")}
            >
              Try Again
            </button>
            <Link href="/dashboard" className="secondary-action-button">
              Return to Dashboard
            </Link>
          </div>
        </div>
      </main>
    );
  }

  // Determine visual style tokens based on real decision
  const isApproved = decision === "APPROVE";
  const isStepUp = decision === "STEP_UP_AUTH";
  const isReclaim = decision === "TRIGGER_RECLAIM";

  return (
    <main className="risk-page">
      <div className="risk-container">
        {/* Header */}
        <header className="risk-top-header">
          <Link
            href="/send/review"
            className="back-button"
            aria-label="Back to Review"
          >
            ←
          </Link>
          <h1>Security Review</h1>
          <div className="header-spacer" />
        </header>

        {/* Hero Section */}
        <section className="risk-hero-section">
          {isApproved && (
            <>
              <div className="security-badge approve">
                <span>✓</span>
                <span>Verified Safe</span>
              </div>
              <h2 className="risk-title">Transaction looks good</h2>
              <p className="risk-subtitle">
                Standard security checks passed. Operational funds are ready for release.
              </p>
            </>
          )}

          {isStepUp && (
            <>
              <div className="security-badge step_up">
                <span>⚠️</span>
                <span>Additional Verification</span>
              </div>
              <h2 className="risk-title">Additional verification required</h2>
              <p className="risk-subtitle">
                We detected transaction characteristics that require secondary verification.
              </p>
            </>
          )}

          {isReclaim && (
            <>
              <h2 className="risk-title">RECLAIM Protection Required</h2>
              <p className="risk-subtitle">
                This transaction needs additional protection before it can be completed.
              </p>
            </>
          )}
        </section>

        {/* Transaction Summary Card */}
        <section className="risk-section">
          <div className="tx-review-card">
            <div className="tx-row">
              <span className="tx-row-label">Transfer Amount</span>
              <span className="tx-row-amount">{formattedAmount}</span>
            </div>

            <div className="tx-divider" />

            <div className="tx-row">
              <span className="tx-row-label">To</span>
              <span className="tx-row-name">{recipientParam}</span>
              <span className="tx-row-account">{recipientAccountParam}</span>
            </div>

            <div className="score-pill-row">
              <span className="score-pill-label">Security Evaluation</span>
              <span
                className={`score-pill ${
                  isApproved ? "low" : isStepUp ? "medium" : "high"
                }`}
              >
                Score: {riskScore} / 100
              </span>
            </div>
          </div>
        </section>

        {/* Risk Indicators (Displayed when returned by the security evaluation) */}
        {riskFactors.length > 0 && (
          <section className="risk-section">
            <div className="indicators-card">
              <div className="indicators-header">
                <span>⚠️</span>
                <span>Identified Security Factors</span>
              </div>
              <ul className="indicators-list">
                {riskFactors.map((factor, index) => (
                  <li key={index} className="indicator-item">
                    <span className="indicator-dot" />
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {/* Protected Money Explanation */}
        <section className="risk-section">
          <div className="protection-guarantee-card">
            <h3 className="protection-guarantee-title">
              Your money is still protected.
            </h3>

            <div className="funds-breakdown">
              <div className="fund-item">
                <span className="fund-item-label">Operational Funds</span>
                <span className="fund-item-amount">
                  ₹{INITIAL_OPERATIONAL_FUNDS.toLocaleString("en-IN")}
                </span>
              </div>

              <div className="fund-item protected-row">
                <span className="fund-item-label">Protected Reserve</span>
                <span className="fund-item-amount">
                  ₹{PROTECTED_RESERVE.toLocaleString("en-IN")}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* RECLAIM Protection Card or Ready to Send Card */}
        {isReclaim && (
          <section className="risk-section">
            <div className="reclaim-protection-card">
              <div className="reclaim-protection-header">
                <span>🛡️</span>
                <span>RECLAIM Protection Active</span>
              </div>
              <p>
                This transaction needs additional protection before it can be completed.
                Your protected reserve safeguards you from unauthorized transfers.
              </p>
            </div>
          </section>
        )}

        {isStepUp && (
          <section className="risk-section">
            <div className="reclaim-protection-card">
              <div className="reclaim-protection-header">
                <span>🔐</span>
                <span>Step-Up Verification Active</span>
              </div>
              <p>
                Because this transaction exceeds normal spending thresholds or involves an
                unfamiliar recipient, additional verification is required before funds can proceed.
              </p>
            </div>
          </section>
        )}

        {isApproved && (
          <section className="risk-section">
            <div className="low-risk-verified-card">
              <div className="low-risk-header">
                <span>✓</span>
                <span>Standard Security Checks Passed</span>
              </div>
              <p>
                This transaction is within operational boundaries. Proceed to
                complete authorization.
              </p>
            </div>
          </section>
        )}

        {/* Bottom Actions */}
        <div className="risk-bottom-action">
          {isApproved && (
            <button className="primary-action-button" onClick={handleContinue}>
              Continue
            </button>
          )}

          {isStepUp && (
            <button className="primary-action-button" onClick={handleContinue}>
              Continue to Verification
            </button>
          )}

          {isReclaim && (
            <button className="primary-action-button" onClick={handleContinue}>
              Continue to Protection
            </button>
          )}

          <Link href="/dashboard" className="secondary-action-button">
            Cancel
          </Link>
        </div>
      </div>
    </main>
  );
}

export default function RiskPage() {
  return (
    <Suspense
      fallback={
        <div className="risk-page">
          <div className="risk-container">
            <div className="risk-loading">Loading security review...</div>
          </div>
        </div>
      }
    >
      <RiskContent />
    </Suspense>
  );
}
