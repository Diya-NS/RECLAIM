"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, useCallback, useMemo, useRef } from "react";
import {
  authorizeHardwareTransaction,
  HardwareAuthorizeResponse,
} from "@/lib/riskEngine";
import "./verify.css";

const DEFAULT_BASE_URL = "http://localhost:8000";

function VerifyContent() {
  const searchParams = useSearchParams();

  const amountParam = searchParams.get("amount");
  const recipientParam = searchParams.get("recipient") || "Beneficiary";
  const recipientAccountParam = searchParams.get("recipientAccount") || "";
  const decision = searchParams.get("decision") || "APPROVE";
  const riskScore = searchParams.get("risk_score") || "0";

  // Stable IDs across re-renders
  const [transactionId] = useState(
    () =>
      searchParams.get("transactionId") ||
      `TXN-${Date.now().toString(36).toUpperCase()}-${Math.random()
        .toString(36)
        .substring(2, 7)
        .toUpperCase()}`
  );
  const [timestamp] = useState(
    () => searchParams.get("timestamp") || new Date().toISOString()
  );

  const challengeId = searchParams.get("challenge_id") || "CHAL-DEFAULT";
  const challengePayload = searchParams.get("challenge_payload") || "payload_default";
  const riskFactorsParam = searchParams.get("risk_factors");

  // Memoize parsed risk factors so reference does not change on every render
  const riskFactors = useMemo(() => {
    if (!riskFactorsParam) return [];
    try {
      return JSON.parse(riskFactorsParam);
    } catch {
      return [];
    }
  }, [riskFactorsParam]);

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
  const [isResetting, setIsResetting] = useState(false);

  // Execution guard: prevents re-running automatically on re-renders
  const hasTriggeredRef = useRef(false);

  const runHardwareAuthorization = useCallback(async () => {
    if (!isReclaim) return;

    setIsAuthorizing(true);
    setAuthError(null);

    const startTime = Date.now();
    // Generate fresh unique nonce per authorization attempt to prevent replay errors
    const freshNonce = `nonce_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    try {
      const res = await authorizeHardwareTransaction({
        transaction_id: transactionId,
        amount: numericAmount,
        recipient: recipientParam,
        sender: "user_101",
        risk_level: "CRITICAL",
        risk_score: Number(riskScore) / 100,
        timestamp,
        nonce: freshNonce,
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

  // Trigger ONCE on mount for TRIGGER_RECLAIM transactions
  useEffect(() => {
    if (isReclaim && !hasTriggeredRef.current) {
      hasTriggeredRef.current = true;
      runHardwareAuthorization();
    }
  }, [isReclaim, runHardwareAuthorization]);

  const handleTryAgain = () => {
    runHardwareAuthorization();
  };

  const handleResetFreezeMode = async () => {
    setIsResetting(true);
    try {
      const baseUrl =
        process.env.NEXT_PUBLIC_RISK_ENGINE_URL || DEFAULT_BASE_URL;
      await fetch(`${baseUrl}/api/v1/hardware/reset`, { method: "POST" });
      setHardwareResult(null);
      setAuthError(null);
      runHardwareAuthorization();
    } catch (e) {
      console.error("Failed to reset hardware state:", e);
    } finally {
      setIsResetting(false);
    }
  };

  const isHardwareApproved = hardwareResult?.status === "APPROVED";
  const isHardwareBlocked = hardwareResult?.status === "BLOCKED";
  const isHardwareFrozen = hardwareResult?.status === "FREEZE_MODE_TRIGGERED";
  const isHardwareUnavailable = hardwareResult?.status === "UNAVAILABLE";

  return (
    <main className="verify-page">
      <div className="verify-container">
        <header className="verify-header">
          <Link href="/send/risk" className="back-button" aria-label="Back">
            ←
          </Link>
          <h1>
            {isHardwareApproved
              ? "Authorization Approved"
              : isApproved
              ? "Authorization"
              : isStepUp
              ? "Verification"
              : "Protection"}
          </h1>
          <div className="header-spacer" />
        </header>

        <section className="verify-hero">
          {/* Visual Status Badge */}
          <div
            className={`verify-badge ${
              isHardwareApproved
                ? "approve"
                : isHardwareBlocked
                ? "step_up"
                : isHardwareFrozen
                ? "reclaim"
                : isApproved
                ? "approve"
                : isStepUp
                ? "step_up"
                : "reclaim"
            }`}
          >
            <span>
              {isHardwareApproved
                ? "✓"
                : isHardwareBlocked
                ? "⚠️"
                : isHardwareFrozen
                ? "🔒"
                : isApproved
                ? "✓"
                : isStepUp
                ? "⚠️"
                : "🛡️"}
            </span>
            <span>
              {isHardwareApproved
                ? "Hardware Authorized"
                : isHardwareBlocked
                ? "Authorization Blocked"
                : isHardwareFrozen
                ? "Security Freeze Active"
                : isAuthorizing
                ? "Awaiting ESP32 Hardware Approval"
                : isApproved
                ? "Standard Approved"
                : isStepUp
                ? "Verification Required"
                : "RECLAIM Security Protocol"}
            </span>
          </div>

          <h2 className="verify-title">
            {isHardwareApproved && "Transfer Successfully Authorized"}
            {isHardwareBlocked && "Hardware Authorization Blocked"}
            {isHardwareFrozen && "Security Freeze Active"}
            {!hardwareResult && isApproved && "Transaction Authorization"}
            {!hardwareResult && isStepUp && "Enhanced Verification Required"}
            {!hardwareResult && isReclaim && "RECLAIM Hardware Security"}
          </h2>

          <p className="verify-subtitle">
            {isHardwareApproved &&
              "Cryptographic proof verified by your ESP32 hardware security enclave. Biometric presence and liveness confirmed."}
            {isHardwareBlocked &&
              "Hardware authorization was rejected or timed out. Your protected funds remain safe in your reserve."}
            {isHardwareFrozen &&
              "3 failed hardware authorization attempts exceeded. Security protection has locked this account to protect all reserves."}
            {!hardwareResult &&
              isApproved &&
              "Your transaction passed standard security evaluation. Final authorization will be performed here."}
            {!hardwareResult &&
              isStepUp &&
              "Elevated risk factors were detected. Step-up authorization will be performed here."}
            {!hardwareResult &&
              isReclaim &&
              "High-risk transfer detected. Cryptographic signing on your ESP32 hardware enclave is required."}
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
            <span className="verify-label">Security Status</span>
            <span
              className={`verify-status ${
                isHardwareApproved ? "approved" : ""
              }`}
            >
              {isHardwareApproved
                ? "✓ Cryptographically Verified & Released"
                : isHardwareBlocked
                ? "⛔ Authorization Blocked"
                : isHardwareFrozen
                ? "🔒 Account Frozen (Funds Preserved)"
                : `Score: ${riskScore} / 100`}
            </span>
          </div>
        </section>

        {/* TRIGGER_RECLAIM: Real Hardware Authorization States */}
        {isReclaim && isAuthorizing && (
          <section className="verify-loading-card">
            <div className="verify-spinner" />
            <p className="verify-loading-text">
              Authorizing with security hardware...
            </p>
            <p className="verify-loading-subtext">
              Verifying challenge <strong>{challengeId}</strong> with ESP32 hardware enclave.
            </p>

            <div className="serial-monitor-hint-box">
              <div className="hint-header">
                <span className="hint-icon">💻</span>
                <span className="hint-title">Action Required in Arduino Serial Monitor</span>
              </div>
              <p className="hint-code">
                Type <strong>&apos;y&apos;</strong> + Enter &rarr; <span>APPROVE &amp; SIGN Challenge</span>
              </p>
              <p className="hint-alt">
                Type <strong>&apos;n&apos;</strong> + Enter &rarr; <span>REJECT (Simulate Biometric Fail)</span>
              </p>
            </div>
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
            {isHardwareApproved && (
              <section className="hardware-result-card approved">
                <div className="result-header-row">
                  <span className="result-header-icon">✓</span>
                  <span className="result-header-title">
                    Hardware Authorization Approved
                  </span>
                </div>
                <p className="result-body-text">
                  Cryptographic proof verified successfully by the ESP32 hardware enclave.
                  Biometric presence and physical liveness confirmed.
                </p>
                <div className="crypto-proof-block">
                  <div className="crypto-proof-item">
                    <span>Challenge ID:</span>
                    <strong>{challengeId}</strong>
                  </div>
                  {hardwareResult.details?.challenge_signature && (
                    <div className="crypto-proof-item">
                      <span>Hardware Signature:</span>
                      <span>
                        {String(hardwareResult.details.challenge_signature).substring(0, 22)}...
                      </span>
                    </div>
                  )}
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
                      <span>Device ID:</span>
                      <span>{hardwareResult.details.device_id}</span>
                    </div>
                  )}
                  <div className="crypto-proof-item">
                    <span>Biometric Enclave Check:</span>
                    <strong style={{ color: "#16a34a" }}>✓ Passed</strong>
                  </div>
                  <div className="crypto-proof-item">
                    <span>Physical Liveness:</span>
                    <strong style={{ color: "#16a34a" }}>✓ Confirmed</strong>
                  </div>
                </div>
              </section>
            )}

            {isHardwareBlocked && (
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

            {isHardwareFrozen && (
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

            {isHardwareUnavailable && (
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
          {/* Try Again on Blocked or Error */}
          {isReclaim &&
            !isAuthorizing &&
            (isHardwareBlocked || authError || isHardwareUnavailable) && (
              <button
                className="verify-primary-button"
                onClick={handleTryAgain}
              >
                Try Again
              </button>
            )}

          {/* Reset button when account hit Freeze Mode during demo/testing */}
          {isReclaim && !isAuthorizing && isHardwareFrozen && (
            <button
              className="verify-primary-button reset-button"
              onClick={handleResetFreezeMode}
              disabled={isResetting}
            >
              {isResetting ? "Resetting Security State..." : "Reset Freeze State (Demo)"}
            </button>
          )}

          {isHardwareApproved ? (
            <>
              <Link href="/dashboard" className="verify-primary-button">
                Done (Return to Dashboard)
              </Link>
              <Link href="/transactions" className="verify-secondary-button">
                View All Transactions
              </Link>
            </>
          ) : (
            <>
              <Link href="/dashboard" className="verify-primary-button">
                Return to Dashboard
              </Link>
              <Link href="/send" className="verify-secondary-button">
                New Transfer
              </Link>
            </>
          )}
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
