"use client";

import Link from "next/link";
import { useState } from "react";
import "./send.css";

const beneficiaries = [
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

export default function SendMoney() {
  const [selectedBeneficiary, setSelectedBeneficiary] =
    useState<number | null>(null);

  const [amount, setAmount] = useState("");

  const selected = beneficiaries.find(
    (beneficiary) =>
      beneficiary.id === selectedBeneficiary
  );

  const numericAmount = Number(amount);

  return (
    <main className="send-page">
      <div className="send-container">

        <header className="send-header">
          <Link href="/dashboard" className="back-button">
            ←
          </Link>

          <h1>Send Money</h1>

          <div className="header-spacer" />
        </header>

        <section className="available-balance">
          <p>Available for spending</p>

          <h2>₹20,000</h2>

          <span>
            Your protected reserve is not available
            for normal transactions.
          </span>
        </section>

        <section className="form-section">
          <div className="section-heading">
            <h2>Send to</h2>

            <button className="manage-button">
              Manage
            </button>
          </div>

          <div className="beneficiary-list">
            {beneficiaries.map((beneficiary) => {
              const isSelected =
                selectedBeneficiary === beneficiary.id;

              return (
                <button
                  key={beneficiary.id}
                  className={`beneficiary ${
                    isSelected ? "selected" : ""
                  }`}
                  onClick={() =>
                    setSelectedBeneficiary(
                      beneficiary.id
                    )
                  }
                >
                  <div className="beneficiary-avatar">
                    {beneficiary.initials}
                  </div>

                  <div className="beneficiary-info">
                    <p>{beneficiary.name}</p>
                    <span>
                      {beneficiary.account}
                    </span>
                  </div>

                  {isSelected && (
                    <div className="check">
                      ✓
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </section>

        <section className="form-section amount-section">
          <label htmlFor="amount">
            Amount
          </label>

          <div className="amount-input-wrapper">
            <span>₹</span>

            <input
              id="amount"
              type="number"
              inputMode="decimal"
              placeholder="0"
              value={amount}
              onChange={(e) =>
                setAmount(e.target.value)
              }
            />
          </div>

          <div className="amount-info">
            <span>Available</span>
            <span>₹20,000</span>
          </div>
        </section>

        <section className="form-section">
          <label htmlFor="note">
            Note <span>(optional)</span>
          </label>

          <input
            id="note"
            className="note-input"
            placeholder="What's this for?"
          />
        </section>

        {selected && numericAmount > 0 && (
          <section className="review-card">

            <div className="review-row">
              <span>Recipient</span>
              <strong>{selected.name}</strong>
            </div>

            <div className="review-row">
              <span>Amount</span>
              <strong>
                ₹{numericAmount.toLocaleString("en-IN")}
              </strong>
            </div>

            <div className="review-row">
              <span>From</span>
              <strong>Operational Funds</strong>
            </div>

          </section>
        )}

        <div className="bottom-action">
          <button
            className="continue-button"
            disabled={
              !selectedBeneficiary ||
              numericAmount <= 0 ||
              numericAmount > 20000
            }
          >
            Review Transaction
          </button>
        </div>

      </div>
    </main>
  );
}