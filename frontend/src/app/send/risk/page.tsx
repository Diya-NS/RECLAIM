"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import {
  INITIAL_OPERATIONAL_FUNDS,
  PROTECTED_RESERVE,
} from "@/data/mockData";
import { RiskLevel, RiskResult } from "@/types/transaction";
import "./risk.css";

const DEFAULT_HIGH_RISK_RESULT: RiskResult = {
  riskScore: 82,
  riskLevel: "HIGH",
  indicators: [
    "Unusual transaction amount",
    "New recipient",
    "Transaction behaviour differs from normal activity",
  ],
};

function RiskContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialLevel: RiskLevel =
    searchParams.get("level")?.toUpperCase() === "LOW" ? "LOW" : "HIGH";

  const [currentLevel, setCurrentLevel] = useState<RiskLevel>(initialLevel);

  const amountParam = searchParams.get("amount");
  const recipientParam = searchParams.get("recipient") || "Rahul";
  const recipientAccountParam =
    searchParams.get("recipientAccount") || "•••• 4821";

  const isHighRisk = currentLevel === "HIGH";

  const numericAmount = amountParam
    ? Number(amountParam)
    : isHighRisk
    ? 100000
    : 2500;
  const formattedAmount = `₹${numericAmount.toLocaleString("en-IN")}`;

  const indicators = DEFAULT_HIGH_RISK_RESULT.indicators || [];

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

        {/* State Switcher for testing LOW vs HIGH risk integration */}
        <div className="state-switcher">
          <button
            className={`switcher-tab ${isHighRisk ? "active" : ""}`}
            onClick={() => setCurrentLevel("HIGH")}
          >
            Elevated Protection (High)
          </button>
          <button
            className={`switcher-tab ${!isHighRisk ? "active" : ""}`}
            onClick={() => setCurrentLevel("LOW")}
          >
            Standard Transfer (Low)
          </button>
        </div>

        {/* Hero Section */}
        <section className="risk-hero-section">
          <div className={`security-badge ${isHighRisk ? "high" : "low"}`}>
            <span>●</span>
            <span>
              {isHighRisk ? "Elevated Protection" : "Standard Verification"}
            </span>
          </div>

          <h2 className="risk-title">
            {isHighRisk
              ? "Transaction needs extra protection"
              : "Transaction verified"}
          </h2>

          <p className="risk-subtitle">
            {isHighRisk
              ? "We detected security factors requiring confirmation before releasing funds."
              : "Standard security checks passed. No additional protection required."}
          </p>
        </section>

        {/* Transaction Summary */}
        <section className="risk-section">
          <div className="tx-review-card">
            <div className="tx-row">
              <span className="tx-row-label">Transaction</span>
              <span className="tx-row-amount">{formattedAmount}</span>
            </div>

            <div className="tx-divider" />

            <div className="tx-row">
              <span className="tx-row-label">To</span>
              <span className="tx-row-name">{recipientParam}</span>
              <span className="tx-row-account">{recipientAccountParam}</span>
            </div>
          </div>
        </section>

        {/* Risk Indicators (Only for HIGH risk state) */}
        {isHighRisk && (
          <section className="risk-section">
            <div className="indicators-card">
              <div className="indicators-header">
                <span>⚠️</span>
                <span>Risk indicators</span>
              </div>
              <ul className="indicators-list">
                {indicators.map((indicator, index) => (
                  <li key={index} className="indicator-item">
                    <span className="indicator-dot" />
                    <span>{indicator}</span>
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

        {/* RECLAIM Protection Card (Prominent Card for High Risk) */}
        {isHighRisk ? (
          <section className="risk-section">
            <div className="reclaim-protection-card">
              <div className="reclaim-protection-header">
                <span>🛡️</span>
                <span>RECLAIM Protection</span>
              </div>
              <p>
                Because this transaction is higher risk, additional verification
                is required before it can be completed.
              </p>
            </div>
          </section>
        ) : (
          <section className="risk-section">
            <div className="low-risk-verified-card">
              <div className="low-risk-header">
                <span>✓</span>
                <span>Ready to Send</span>
              </div>
              <p>
                This transaction meets standard safety guidelines. You may proceed
                with completing the payment directly.
              </p>
            </div>
          </section>
        )}

        {/* Bottom Actions */}
        <div className="risk-bottom-action">
          {isHighRisk ? (
            <button
              className="primary-action-button"
              onClick={() => router.push("/send/verify")}
            >
              Continue to Verification
            </button>
          ) : (
            <button
              className="primary-action-button"
              onClick={() => router.push("/dashboard")}
            >
              Complete Transfer
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
