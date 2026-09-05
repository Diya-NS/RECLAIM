"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, useCallback } from "react";
import { beneficiaries } from "@/data/mockData";
import { evaluateTransaction } from "@/lib/riskEngine";
import "./check.css";

function CheckContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const amountParam = searchParams.get("amount");
  const recipientParam = searchParams.get("recipient");
  const recipientAccountParam = searchParams.get("recipientAccount");
  const beneficiaryIdParam = searchParams.get("beneficiaryId");
  const noteParam = searchParams.get("note") || "";
  const transactionIdParam = searchParams.get("transactionId") || "";
  const timestampParam = searchParams.get("timestamp") || "";

  const fallbackBeneficiary =
    beneficiaries.find((b) => String(b.id) === beneficiaryIdParam) ||
    beneficiaries[0];

  const recipient = recipientParam || fallbackBeneficiary.name;
  const recipientAccount = recipientAccountParam || fallbackBeneficiary.account;
  const numericAmount = Number(amountParam) > 0 ? Number(amountParam) : 2500;
  const formattedAmount = `₹${numericAmount.toLocaleString("en-IN")}`;
  const beneficiaryId = beneficiaryIdParam || String(fallbackBeneficiary.id);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const runEvaluation = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const startTime = Date.now();

    try {
      const evaluation = await evaluateTransaction({
        amount: numericAmount,
        recipientId: beneficiaryId,
      });

      // Maintain smooth animation pacing for ~700ms
      const elapsed = Date.now() - startTime;
      const delay = Math.max(0, 700 - elapsed);
      await new Promise((resolve) => setTimeout(resolve, delay));

      const params = new URLSearchParams({
        amount: String(numericAmount),
        recipient,
        recipientAccount,
        beneficiaryId: String(beneficiaryId),
        ...(transactionIdParam ? { transactionId: transactionIdParam } : {}),
        ...(timestampParam ? { timestamp: timestampParam } : {}),
        ...(noteParam ? { note: noteParam } : {}),
        risk_score: String(evaluation.risk_score),
        decision: evaluation.decision,
        risk_factors: JSON.stringify(evaluation.risk_factors),
        breakdown: JSON.stringify(evaluation.breakdown),
        ...(evaluation.challenge_id ? { challenge_id: evaluation.challenge_id } : {}),
        ...(evaluation.challenge_payload ? { challenge_payload: evaluation.challenge_payload } : {}),
      });

      router.push(`/send/risk?${params.toString()}`);
    } catch (err) {
      console.error("Security check failed:", err);
      setIsLoading(false);
      setError("Transaction check unavailable. Please try again.");
    }
  }, [
    numericAmount,
    beneficiaryId,
    recipient,
    recipientAccount,
    transactionIdParam,
    timestampParam,
    noteParam,
    router,
  ]);

  useEffect(() => {
    runEvaluation();
  }, [runEvaluation]);

  return (
    <main className="check-page">
      <div className="check-container">
        <section className="security-hero">
          <div className="animation-container">
            {isLoading && (
              <>
                <div className="pulse-ring" />
                <div className="pulse-ring-second" />
                <div className="spinner-arc" />
              </>
            )}
            <div className={`status-icon-circle ${error ? "error" : ""}`}>
              <span>{error ? "!" : "🛡️"}</span>
            </div>
          </div>

          <h1 className="check-title">
            {error ? "Security Check Unavailable" : "Checking your transaction..."}
          </h1>

          <p className="check-subtitle">
            {error
              ? "We could not complete the security verification at this time."
              : "We're making sure this transaction is safe before it goes through."}
          </p>

          {error && (
            <div className="check-error-box">
              <p className="check-error-title">Transaction check unavailable. Please try again.</p>
            </div>
          )}
        </section>

        <section className="transaction-check-card">
          <div className="detail-block">
            <span className="detail-label">Transaction</span>
            <span className="detail-amount">{formattedAmount}</span>
          </div>

          <div className="card-divider" />

          <div className="detail-block">
            <span className="detail-label">To</span>
            <span className="detail-name">{recipient}</span>
            <span className="detail-account">{recipientAccount}</span>
          </div>

          <div className="card-divider" />

          <div className="detail-block">
            <span className="detail-label">From</span>
            <span className="detail-from">Operational Funds</span>
          </div>
        </section>

        <div className="check-spacer" />

        <div className="check-bottom-area">
          {error ? (
            <div className="check-actions">
              <button className="retry-button" onClick={runEvaluation}>
                Try Again
              </button>
              <Link href="/send/review" className="back-link-button">
                Back to Review
              </Link>
            </div>
          ) : (
            <div className="security-badge-footer">
              <span>RECLAIM Transaction Verification</span>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

export default function CheckPage() {
  return (
    <Suspense
      fallback={
        <div className="check-page">
          <div className="check-container">
            <div className="check-loading">
              Loading transaction security check...
            </div>
          </div>
        </div>
      }
    >
      <CheckContent />
    </Suspense>
  );
}
