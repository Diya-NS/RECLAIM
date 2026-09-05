"""
RECLAIM Hardware Authorization Subsystem Demo
Person 3: Hardware responsibility

Demonstrates Integration with:
- Person 2 (Risk Engine decision: "TRIGGER_RECLAIM" + risk_factors)
- Person 3 (ESP32 Hardware-backed Biometric / Cryptographic Proof)
- Person 4 (Freeze Mode triggered on 3 failed attempts)
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from hardware.simulator.esp32_simulator import ESP32DeviceHardware
from src.hardware_auth import (
    RiskLevel,
    RiskDecision,
    TransactionPayload,
    HardwareClient,
    SignatureVerifier,
    HardwareAuthorizationService,
    AuthorizationStatus,
)


def mock_person4_compromise_recovery(tx: TransactionPayload, ver_res):
    print("\n  [PERSON 4 - FREEZE MODE & RECOVERY PROTOCOL TRIGGERED]")
    print(f"     Status:          ACCOUNT FROZEN - 3 FAILED HARDWARE ATTEMPTS")
    print(f"     Target User:     {tx.sender}")
    print(f"     Suspicious Tx:   {tx.transaction_id} (Amount: ${tx.amount:,.2f})")
    print(f"     Risk Factors:    {', '.join(tx.risk_factors)}")
    print(f"     Failure Reason:  {ver_res.reason}")
    print(f"     Action Taken:    Account & Reserved Funds Locked. Email/SMS Alert Dispatched.\n")


def main():
    print("=========================================================================")
    print(" RECLAIM - Person 3 Hardware Subsystem (TRIGGER_RECLAIM & Freeze Mode)")
    print("=========================================================================\n")

    # Initialize Hardware Device & Service
    esp32_device = ESP32DeviceHardware(device_id="ESP32-HARDWARE-SECURE-ELEMENT-01")
    print(f"[HARDWARE SETUP] ESP32 Device Initialized.")
    print(f"  Public Key: {esp32_device.public_key[:36]}...\n")

    client = HardwareClient(direct_hardware_device=esp32_device)
    verifier = SignatureVerifier()
    verifier.register_trusted_device_key(esp32_device.public_key)

    service = HardwareAuthorizationService(
        hardware_client=client,
        signature_verifier=verifier,
        person4_compromise_handler=mock_person4_compromise_recovery,
        max_allowed_failed_attempts=3,
    )

    time.sleep(0.3)

    # -------------------------------------------------------------------------
    # SCENARIO 1: Person 2 Decision TRIGGER_RECLAIM -> Hardware Auth PASSES
    # -------------------------------------------------------------------------
    print("-------------------------------------------------------------------------")
    print("SCENARIO 1: Person 2 Decision 'TRIGGER_RECLAIM' (Protected Reserve Access)")
    print("-------------------------------------------------------------------------")
    esp32_device.simulate_biometric_pass = True
    esp32_device.simulate_liveness_pass = True

    tx1 = TransactionPayload(
        transaction_id="TX-2001-PROTECTED-RESERVE",
        amount=18500.00,
        recipient="vault_exchange",
        sender="user_alice",
        risk_level=RiskLevel.HIGH,
        risk_score=0.92,
        timestamp="2026-09-05T22:30:00Z",
        nonce="nonce_reclaim_1001",
        risk_decision=RiskDecision.TRIGGER_RECLAIM.value,
        risk_factors=["amount_exceeded", "protected_reserve_accessed"],
    )

    res1 = service.process_transaction_authorization(tx1)
    if res1.is_valid:
        print(" -> RESULT: Transfer Processed Successfully with Hardware Signature Proof!\n")

    time.sleep(0.3)

    # -------------------------------------------------------------------------
    # SCENARIO 2: 3 Failed Hardware Attempts -> Triggers Person 4 FREEZE MODE
    # -------------------------------------------------------------------------
    print("-------------------------------------------------------------------------")
    print("SCENARIO 2: User 'attacker_bob' — 3 Failed Hardware Attempts -> FREEZE MODE")
    print("-------------------------------------------------------------------------")
    esp32_device.simulate_biometric_pass = False  # Simulate biometric fail on ESP32

    for attempt in range(1, 4):
        print(f"\n--- Attempt {attempt} of 3 ---")
        tx_fail = TransactionPayload(
            transaction_id=f"TX-300{attempt}-ATTACK",
            amount=50000.00,
            recipient="offshore_acc",
            sender="attacker_bob",
            risk_level=RiskLevel.CRITICAL,
            risk_score=0.98,
            timestamp=f"2026-09-05T22:3{attempt}:00Z",
            nonce=f"nonce_attack_0{attempt}",
            risk_decision=RiskDecision.TRIGGER_RECLAIM.value,
            risk_factors=["unrecognized_device", "amount_exceeded"],
        )
        service.process_transaction_authorization(tx_fail)
        time.sleep(0.3)

    print("=========================================================================")
    print(" DEMONSTRATION COMPLETE — Person 2 TRIGGER_RECLAIM & Freeze Mode Verified!")
    print("=========================================================================")


if __name__ == "__main__":
    main()
