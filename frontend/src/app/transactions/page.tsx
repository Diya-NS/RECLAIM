"use client";

import Link from "next/link";
import { useState } from "react";
import { mockTransactions, TOTAL_BALANCE } from "@/data/mockData";
import "./transactions.css";

type FilterType = "all" | "sent" | "received";

export default function TransactionsPage() {
  const [filter, setFilter] = useState<FilterType>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filteredTransactions = mockTransactions.filter((tx) => {
    if (filter === "sent") {
      return tx.amount < 0;
    }
    if (filter === "received") {
      return tx.amount > 0;
    }
    return true;
  });

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <main className="transactions-page">
      <div className="transactions-container">
        {/* Header */}
        <header className="tx-header">
          <Link href="/dashboard" className="back-button" aria-label="Back to Dashboard">
            ←
          </Link>
          <h1>Transactions</h1>
          <div className="header-spacer" />
        </header>

        {/* Balance Summary */}
        <section className="tx-balance-section">
          <div className="tx-balance-card">
            <p className="tx-balance-label">Total Balance</p>
            <h2 className="tx-balance-amount">
              ₹{TOTAL_BALANCE.toLocaleString("en-IN")}
            </h2>
          </div>
        </section>

        {/* Filter Controls */}
        <section className="filter-bar">
          <button
            className={`filter-pill ${filter === "all" ? "active" : ""}`}
            onClick={() => setFilter("all")}
          >
            All
          </button>
          <button
            className={`filter-pill ${filter === "sent" ? "active" : ""}`}
            onClick={() => setFilter("sent")}
          >
            Sent
          </button>
          <button
            className={`filter-pill ${filter === "received" ? "active" : ""}`}
            onClick={() => setFilter("received")}
          >
            Received
          </button>
        </section>

        {/* Transactions List */}
        <section className="tx-list-section">
          {filteredTransactions.length === 0 ? (
            <div className="tx-empty">No transactions found.</div>
          ) : (
            <div className="tx-list">
              {filteredTransactions.map((tx) => {
                const isReceived = tx.amount > 0;
                const isExpanded = expandedId === tx.id;

                return (
                  <div
                    key={tx.id}
                    className={`tx-card ${isExpanded ? "expanded" : ""}`}
                    onClick={() => toggleExpand(tx.id)}
                  >
                    <div className="tx-main-row">
                      <div className="tx-left">
                        <div className="tx-avatar">
                          {tx.name.charAt(0)}
                        </div>
                        <div className="tx-name-group">
                          <span className="tx-name">{tx.name}</span>
                          <span className="tx-meta">
                            {tx.type} · {tx.date}
                          </span>
                        </div>
                      </div>

                      <div className="tx-right">
                        <span
                          className={`tx-amount ${
                            isReceived ? "received" : ""
                          }`}
                        >
                          {isReceived ? "+" : "-"}₹
                          {Math.abs(tx.amount).toLocaleString("en-IN")}
                        </span>
                        <span className="tx-status-badge">
                          {tx.status}
                        </span>
                      </div>
                    </div>

                    {/* Expandable Transaction Details */}
                    {isExpanded && (
                      <div className="tx-expanded-details">
                        <div className="detail-row">
                          <span>Account / Channel</span>
                          <strong className="detail-account-code">
                            {tx.account || "Operational Funds"}
                          </strong>
                        </div>
                        <div className="detail-row">
                          <span>Status</span>
                          <strong>{tx.status}</strong>
                        </div>
                        {tx.note && (
                          <div className="detail-row">
                            <span>Note</span>
                            <strong>{tx.note}</strong>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Bottom Navigation */}
        <nav className="bottom-nav">
          <Link href="/dashboard" className="nav-item">
            <span>⌂</span>
            Home
          </Link>

          <Link href="/send" className="nav-item">
            <span>↗</span>
            Payments
          </Link>

          <Link href="/transactions" className="nav-item active">
            <span>◷</span>
            Activity
          </Link>

          <button className="nav-item">
            <span>○</span>
            Profile
          </button>
        </nav>
      </div>
    </main>
  );
}
