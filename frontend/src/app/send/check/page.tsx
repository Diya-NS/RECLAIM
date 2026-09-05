"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { beneficiaries } from "@/data/mockData";
import "./check.css";

function CheckContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const amountParam = searchParams.get("amount");
  const recipientParam = searchParams.get("recipient");
  const recipientAccountParam = searchParams.get("recipientAccount");
  const beneficiaryIdParam = searchParams.get("beneficiaryId");

  const fallbackBeneficiary =
    beneficiaries.find((b) => String(b.id) === beneficiaryIdParam) ||
    beneficiaries[0];

  const recipient = recipientParam || fallbackBeneficiary.name;
  const recipientAccount = recipientAccountParam || fallbackBeneficiary.account;
  const numericAmount = Number(amountParam) > 0 ? Number(amountParam) : 2500;
  const formattedAmount = `₹${numericAmount.toLocaleString("en-IN")}`;

  useEffect(() => {
    const timer = setTimeout(() => {
      const params = new URLSearchParams({
        amount: String(numericAmount),
        recipient,
        recipientAccount,
        beneficiaryId: String(fallbackBeneficiary.id),
        ...(searchParams.get("note") ? { note: searchParams.get("note")! } : {}),
      });
      router.push(`/send/risk?${params.toString()}`);
    }, 1800);

    return () => clearTimeout(timer);
  }, [numericAmount, recipient, recipientAccount, fallbackBeneficiary.id, searchParams, router]);

  return (
    <main className="check-page">
      <div className="check-container">
        <section className="security-hero">
          <div className="animation-container">
            <div className="pulse-ring" />
            <div className="pulse-ring-second" />
            <div className="spinner-arc" />
            <div className="status-icon-circle">
              <span>..</span>
            </div>
          </div>

          <h1 className="check-title">Checking your transaction...</h1>

          <p className="check-subtitle">
            We're making sure this transaction is safe before it goes through.
          </p>
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
          <div className="security-badge-footer">
            <span>RECLAIM Transaction Verification</span>
          </div>
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
