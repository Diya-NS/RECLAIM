"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, useCallback } from "react";
import {
  authorizeHardwareTransaction,
  HardwareAuthorizeResponse,
} from "@/lib/riskEngine";
import "./verify.css";

function VerifyContent() {
  const searchParams = useSearchParams();

  const amountParam = searchParams.get("amount");
  const recipientParam = searchParams.get("recipient") || "Beneficiary";
  const recipientAccountParam = searchParams.get("recipientAccount") || "";
  const decision = searchParams.get("decision") || "APPROVE";
  const riskScore = searchParams.get("risk_score") || "0";
  const transactionId = searchParams.get("transactionId") || `TXN-${Date.now()}`;
  const timestamp = searchParams.get("timestamp") || new Date().toISOString();
  const challengeId = searchParams.get("challenge_id") || "CHAL-DEFAULT";
  const challengePayload = searchParams.get("challenge_payload") || "payload_default";
  const riskFactorsParam = searchParams.get("risk_factors");

  let riskFactors: string[] = [];
  if (riskFactorsParam) {
    try {
      riskFactors = JSON.parse(riskFactorsParam);
    } catch {
      riskFactors = [];
    }
  }

  const numericAmount = Number(amountParam) > 0 ? Number(amountParam) : 2000;
  const formattedAmount = `₹${numericAmount.toLocaleString("en-IN")}`;

  const isApproved = decision === "APPROVE";
  const isStepUp = decision === "STEP_UP_AUTH";
  const isReclaim = decision === "TRIGGER_RECLAIM";

  // Hardware authorization states for TRIGGER_RECLAIM
  const [isAuthorizing, setIsAuthorizing] = useState(isReclaim);
  const [hardwareResult, setHardwareResult] =
    useState<HardwareAuthorizeResponse | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  const runHardwareAuthorization = useCallback(async () => {
    if (!isReclaim) return;

    setIsAuthorizing(true);
    setAuthError(null);

    const startTime = Date.now();

    try {
      const res = await authorizeHardwareTransaction({
        transaction_id: transactionId,
        amount: numericAmount,
        recipient: recipientParam,
        sender: "user_101",
        risk_level: "CRITICAL",
        risk_score: Number(riskScore) / 100,
        timestamp,
        risk_decision: "TRIGGER_RECLAIM",
        risk_factors: riskFactors,
        challenge_id: challengeId,
        challenge_payload: challengePayload,
      });

      // Smooth visual pacing (~700ms minimum)
      const elapsed = Date.now() - startTime;
      const delay = Math.max(0, 700 - elapsed);
      await new Promise((resolve) => setTimeout(resolve, delay));

      setHardwareResult(res);
      setIsAuthorizing(false);
    } catch (err: any) {
      console.error("Hardware authorization failed:", err);
      setIsAuthorizing(false);
      setAuthError("Security authorization unavailable. Please try again.");
    }
  }, [
    isReclaim,
    transactionId,
    numericAmount,
    recipientParam,
    riskScore,
    timestamp,
    riskFactors,
    challengeId,
    challengePayload,
  ]);

  useEffect(() => {
    if (isReclaim) {
      runHardwareAuthorization();
    }
  }, [isReclaim, runHardwareAuthorization]);

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
              "High-risk transfer detected. Hardware-backed security proof is required before funds can proceed."}
          </p>
        </section>

        {/* Transaction Details Card */}
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

        {/* TRIGGER_RECLAIM: Real Hardware Authorization Results */}
        {isReclaim && isAuthorizing && (
          <section className="verify-loading-card">
            <div className="verify-spinner" />
            <p className="verify-loading-text">
              Authorizing with security hardware...
            </p>
            <p className="verify-loading-subtext">
              Verifying challenge {challengeId} with secure hardware enclave.
            </p>
          </section>
        )}

        {isReclaim && !isAuthorizing && authError && (
          <section className="hardware-result-card unavailable">
            <div className="result-header-row">
              <span className="result-header-icon">⚠️</span>
              <span className="result-header-title">
                Security authorization unavailable. Please try again.
              </span>
            </div>
            <p className="result-body-text">
              Could not communicate with the security hardware enclave. The
              transaction remains safe and has not been processed.
            </p>
          </section>
        )}

        {isReclaim && !isAuthorizing && hardwareResult && (
          <>
            {hardwareResult.status === "APPROVED" && (
              <section className="hardware-result-card approved">
                <div className="result-header-row">
                  <span className="result-header-icon">✓</span>
                  <span className="result-header-title">
                    Hardware Authorization Approved
                  </span>
                </div>
                <p className="result-body-text">
                  Cryptographic proof verified successfully by the hardware enclave.
                  Biometric presence and physical liveness confirmed.
                </p>
                <div className="crypto-proof-block">
                  <div className="crypto-proof-item">
                    <span>Challenge ID:</span>
                    <strong>{challengeId}</strong>
                  </div>
                  {hardwareResult.details?.public_key && (
                    <div className="crypto-proof-item">
                      <span>Public Key:</span>
                      <span>
                        {String(hardwareResult.details.public_key).substring(0, 18)}...
                      </span>
                    </div>
                  )}
                  {hardwareResult.details?.device_id && (
                    <div className="crypto-proof-item">
                      <span>Device:</span>
                      <span>{hardwareResult.details.device_id}</span>
                    </div>
                  )}
                </div>
              </section>
            )}

            {hardwareResult.status === "BLOCKED" && (
              <section className="hardware-result-card blocked">
                <div className="result-header-row">
                  <span className="result-header-icon">⛔</span>
                  <span className="result-header-title">
                    Security Authorization Blocked
                  </span>
                </div>
                <p className="result-body-text">
                  {hardwareResult.reason ||
                    "Hardware authorization failed. Your funds remain safe in your reserve."}
                </p>
                <div className="strike-pills-row">
                  <span className="strike-label">
                    Strike {hardwareResult.failed_attempts_count} of 3:
                  </span>
                  <div
                    className={`strike-dot ${
                      hardwareResult.failed_attempts_count >= 1 ? "active" : ""
                    }`}
                  />
                  <div
                    className={`strike-dot ${
                      hardwareResult.failed_attempts_count >= 2 ? "active" : ""
                    }`}
                  />
                  <div
                    className={`strike-dot ${
                      hardwareResult.failed_attempts_count >= 3 ? "active" : ""
                    }`}
                  />
                </div>
              </section>
            )}

            {hardwareResult.status === "FREEZE_MODE_TRIGGERED" && (
              <section className="hardware-result-card frozen">
                <div className="result-header-row">
                  <span className="result-header-icon">🔒</span>
                  <span className="result-header-title">
                    Security Freeze Mode Active
                  </span>
                </div>
                <p className="result-body-text">
                  3 failed hardware authorization attempts exceeded. Security
                  protection has locked this account and preserved all funds.
                </p>
                <div className="strike-pills-row">
                  <span className="strike-label">Strikes:</span>
                  <div className="strike-dot active" />
                  <div className="strike-dot active" />
                  <div className="strike-dot active" />
                </div>
              </section>
            )}

            {hardwareResult.status === "UNAVAILABLE" && (
              <section className="hardware-result-card unavailable">
                <div className="result-header-row">
                  <span className="result-header-icon">⚠️</span>
                  <span className="result-header-title">
                    Security authorization unavailable. Please try again.
                  </span>
                </div>
                <p className="result-body-text">
                  {hardwareResult.reason ||
                    "The hardware device is currently offline or unreachable."}
                </p>
              </section>
            )}
          </>
        )}

        {/* Placeholders for APPROVE and STEP_UP_AUTH */}
        {!isReclaim && (
          <section className="notice-box">
            <div className="notice-icon">🛡️</div>
            <div className="notice-content">
              <strong>Security Check Passed</strong>
              <p>
                Initial risk assessment complete. Next-stage authorization
                protocol will be configured in subsequent steps. No funds have
                been debited.
              </p>
            </div>
          </section>
        )}

        <div className="verify-spacer" />

        <div className="verify-actions">
          {isReclaim && !isAuthorizing && (hardwareResult?.status === "BLOCKED" || authError || hardwareResult?.status === "UNAVAILABLE") && (
            <button
              className="verify-primary-button"
              onClick={runHardwareAuthorization}
            >
              Try Again
            </button>
          )}

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
