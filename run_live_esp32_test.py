"""
Live Physical ESP32 Integration Test Script
Person 2 -> Person 3 (Physical ESP32 over Wi-Fi) -> Person 4

Usage:
  python run_live_esp32_test.py <ESP32_IP_ADDRESS>

Example:
  python run_live_esp32_test.py 192.168.1.50
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.hardware_auth import (
    RiskLevel,
    RiskDecision,
    TransactionPayload,
    HardwareClient,
    SignatureVerifier,
    HardwareAuthorizationService,
    AuthorizationStatus,
)
from src.compromise_recovery import (
    CompromiseEngine,
    NotificationDispatcher,
    RecoveryService,
    RecoveryRequest,
)


def mock_person4_handler(tx, ver_res):
    print("\n  [PERSON 4 - FREEZE MODE TRIGGERED ON PHYSICAL HARDWARE FAILURE]")
    print(f"     Target User:    {tx.sender}")
    print(f"     Tx ID:          {tx.transaction_id}")
    print(f"     Reason:         {ver_res.reason}")
    print(f"     Status:         ACCOUNT FROZEN & EMERGENCY ALERTS DISPATCHED\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_live_esp32_test.py <ESP32_IP_ADDRESS>")
        print("Example: python run_live_esp32_test.py 192.168.1.50")
        return

    esp32_ip = sys.argv[1].replace("http://", "").rstrip("/")
    endpoint_url = f"http://{esp32_ip}"

    print("=========================================================================")
    print(" RECLAIM - Live Physical ESP32 Hardware Integration Test")
    print("=========================================================================")
    print(f"[CONNECTING] Connecting to ESP32 at {endpoint_url}...")

    client = HardwareClient(endpoint_url=endpoint_url)

    # 1. Fetch Status & Public Key from physical ESP32
    status = client.get_device_status()
    if "error" in status or status.get("online") is False:
        print(f"[ERROR] Could not connect to ESP32 at {endpoint_url}.")
        print(f"  Error details: {status.get('error')}")
        print("  Make sure your laptop and ESP32 are connected to 'Startathon_wifi'!")
        return

    pub_key = status.get("public_key", "")
    device_id = status.get("device_id", "ESP32")
    print(f"\n[ESP32 CONNECTED SUCCESSFULLY!]")
    print(f"  Device ID:  {device_id}")
    print(f"  Public Key: {pub_key[:36]}...")

    # 2. Setup Verifier & Services
    verifier = SignatureVerifier()
    verifier.register_trusted_device_key(pub_key)

    engine = CompromiseEngine()
    hw_service = HardwareAuthorizationService(
        hardware_client=client,
        signature_verifier=verifier,
        person4_compromise_handler=mock_person4_handler,
        max_allowed_failed_attempts=3,
    )

    # 3. Create Live Person 2 "TRIGGER_RECLAIM" Challenge
    tx = TransactionPayload(
        transaction_id="TX-LIVE-8801",
        amount=12500.00,
        recipient="vault_exchange",
        sender="alice",
        risk_level=RiskLevel.HIGH,
        risk_score=0.94,
        timestamp="2026-09-06T01:00:00Z",
        nonce="nonce_live_8801",
        risk_decision=RiskDecision.TRIGGER_RECLAIM.value,
        risk_factors=["protected_reserve_accessed", "amount_exceeded"],
        challenge_id="CHAL-LIVE-99",
        challenge_payload="a1b2c3d4e5f67890",
    )

    print("\n-------------------------------------------------------------------------")
    print("SENDING PERSON 2 'TRIGGER_RECLAIM' CHALLENGE TO PHYSICAL ESP32...")
    print("-------------------------------------------------------------------------")
    print(f"  Challenge ID:      {tx.challenge_id}")
    print(f"  Challenge Payload: {tx.challenge_payload}")
    print("\nINSTRUCTIONS:")
    print("  Check Arduino IDE Serial Monitor for your ESP32 board:")
    print("  -> Type 'y' + Enter to APPROVE & SIGN on Physical ESP32")
    print("  -> Type 'n' + Enter to REJECT / SIMULATE BIOMETRIC FAIL")
    print("-------------------------------------------------------------------------\n")

    res = hw_service.process_transaction_authorization(tx)

    print("\n=========================================================================")
    print(f" FINAL RESULT: {res.status.value}")
    print(f" Reason:       {res.reason}")
    print("=========================================================================")


if __name__ == "__main__":
    main()
