"use client";

import Link from "next/link";
import "./dashboard.css";

const transactions = [
  {
    name: "Rahul",
    type: "Sent",
    amount: -2000,
    date: "Today, 10:42 AM",
  },
  {
    name: "Swiggy",
    type: "Payment",
    amount: -450,
    date: "Today, 9:18 AM",
  },
  {
    name: "Salary",
    type: "Received",
    amount: 45000,
    date: "Yesterday",
  },
];

export default function Dashboard() {
  const totalBalance = 200000;
  const operationalFunds = 20000;
  const protectedReserve = 180000;

  return (
    <main className="dashboard-page">
      <div className="dashboard-container">

        {/* Header */}
        <header className="dashboard-header">
          <div>
            <p className="greeting">Good morning</p>
            <h1>Welcome back</h1>
          </div>

          <button className="profile-button">
            👤
          </button>
        </header>

        {/* Balance */}
        <section className="balance-section">
          <p className="section-label">Total Balance</p>

          <h2 className="total-balance">
            ₹{totalBalance.toLocaleString("en-IN")}
          </h2>
        </section>

        {/* Funds */}
        <section className="funds-grid">

          <div className="fund-card operational">
            <p className="fund-label">
              Operational Funds
            </p>

            <h3>
              ₹{operationalFunds.toLocaleString("en-IN")}
            </h3>

            <p className="fund-description">
              Available for spending
            </p>
          </div>

          <div className="fund-card protected">
            <div className="protected-title">
              <p className="fund-label">
                Protected Reserve
              </p>
            </div>

            <h3>
              ₹{protectedReserve.toLocaleString("en-IN")}
            </h3>

            <p className="fund-description">
              Protected funds
            </p>
          </div>

        </section>

        {/* Quick Actions */}
        <section className="quick-actions">

          <Link
            href="/send"
            className="action-button primary"
          >
            Send Money
          </Link>

          <button className="action-button secondary">
            Receive Money
          </button>

        </section>

        {/* Recent Transactions */}
        <section className="transactions-section">

          <div className="section-header">
            <h2>Recent Transactions</h2>

            <Link href="/transactions">
              View all
            </Link>
          </div>

          <div className="transaction-list">

            {transactions.map((transaction) => {
              const received = transaction.amount > 0;

              return (
                <div
                  className="transaction"
                  key={`${transaction.name}-${transaction.date}`}
                >

                  <div className="transaction-left">

                    <div className="transaction-avatar">
                      {transaction.name.charAt(0)}
                    </div>

                    <div>
                      <p className="transaction-name">
                        {transaction.name}
                      </p>

                      <p className="transaction-info">
                        {transaction.type} ·{" "}
                        {transaction.date}
                      </p>
                    </div>

                  </div>

                  <p
                    className={`transaction-amount ${
                      received ? "received" : ""
                    }`}
                  >
                    {received ? "+" : "-"}₹
                    {Math.abs(transaction.amount).toLocaleString(
                      "en-IN"
                    )}
                  </p>

                </div>
              );
            })}

          </div>

        </section>

        {/* Bottom Navigation */}
        <nav className="bottom-nav">

          <Link
            href="/dashboard"
            className="nav-item active"
          >
            <span>⌂</span>
            Home
          </Link>

          <Link
            href="/send"
            className="nav-item"
          >
            <span>↗</span>
            Payments
          </Link>

          <Link
            href="/transactions"
            className="nav-item"
          >
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