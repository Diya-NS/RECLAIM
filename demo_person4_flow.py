"""
RECLAIM Subsystem Demonstration — Person 4: Compromise, Freeze & Account Recovery
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
)
from src.compromise_recovery import (
    AccountStatus,
    CompromiseEngine,
    NotificationDispatcher,
    RecoveryService,
    RecoveryRequest,
)


def main():
    print("=========================================================================")
    print(" RECLAIM — Person 4 Compromise, Freeze & Account Recovery Subsystem")
    print("=========================================================================\n")

    # 1. Setup Person 4 Engine & Dispatcher
    dispatcher = NotificationDispatcher()
    engine = CompromiseEngine(notification_dispatcher=dispatcher)
    recovery_service = RecoveryService(compromise_engine=engine)

    # 2. Setup ESP32 Hardware Device & Person 3 Hardware Auth Service
    esp32_device = ESP32DeviceHardware(device_id="ESP32-SECURE-ENCLAVE-01")
    client = HardwareClient(direct_hardware_device=esp32_device)
    verifier = SignatureVerifier()
    verifier.register_trusted_device_key(esp32_device.public_key)

    # Wire Person 4's failure handler into Person 3's service
    hw_service = HardwareAuthorizationService(
        hardware_client=client,
        signature_verifier=verifier,
        person4_compromise_handler=engine.handle_person3_hardware_failure_event,
        max_allowed_failed_attempts=3,
    )

    time.sleep(0.3)

    # -------------------------------------------------------------------------
    # STAGE 1: Suspicious Activity / 3 Failed Hardware Attempts Trigger Freeze
    # -------------------------------------------------------------------------
    print("-------------------------------------------------------------------------")
    print("STAGE 1: Unauthorized Transfer Attempt on Account 'user_alice'")
    print("-------------------------------------------------------------------------")
    esp32_device.simulate_biometric_pass = False  # Simulate fingerprint mismatch

    for attempt in range(1, 4):
        print(f"\n[ATTEMPT {attempt}/3]")
        tx = TransactionPayload(
            transaction_id=f"TX-ATTACK-00{attempt}",
            amount=45000.00,
            recipient="unknown_offshore_wallet",
            sender="alice",
            risk_level=RiskLevel.CRITICAL,
            risk_score=0.98,
            timestamp=f"2026-09-06T00:1{attempt}:00Z",
            nonce=f"nonce_attack_00{attempt}",
            risk_decision=RiskDecision.TRIGGER_RECLAIM.value,
            risk_factors=["unrecognized_device", "protected_reserve_accessed"],
            challenge_id=f"CHAL-ATTACK-00{attempt}",
            challenge_payload=f"payload_attack_00{attempt}",
        )
        hw_service.process_transaction_authorization(tx)
        time.sleep(0.3)

    # Verify Account Status
    print(f"\n[CURRENT ACCOUNT STATUS]: {engine.get_account_status('alice').value}")

    time.sleep(0.5)

    # -------------------------------------------------------------------------
    # STAGE 2: Inspect Dispatched Security Alerts & Recovery Credentials
    # -------------------------------------------------------------------------
    print("\n-------------------------------------------------------------------------")
    print("STAGE 2: Dispatched Security Notifications & Emergency Credentials")
    print("-------------------------------------------------------------------------")
    alice_notifs = [n for n in dispatcher.dispatched_notifications if n.user_id == "alice"]
    email_notif = [n for n in alice_notifs if n.channel == "EMAIL"][0]
    sms_notif = [n for n in alice_notifs if n.channel == "SMS"][0]

    print(f"  Received Email Alert: '{email_notif.title}'")
    print(f"  Received SMS Alert:   '{sms_notif.message}'")
    print(f"  Extracted OTP Code:    [{email_notif.otp_code}]")
    print(f"  Extracted Token:       [{email_notif.recovery_token}]")

    time.sleep(0.5)

    # -------------------------------------------------------------------------
    # STAGE 3: User Executes Multi-Factor Account Recovery & Unfreeze
    # -------------------------------------------------------------------------
    print("\n-------------------------------------------------------------------------")
    print("STAGE 3: Multi-Factor Account Recovery Protocol (OTP + ESP32 Hardware Proof)")
    print("-------------------------------------------------------------------------")
    esp32_device.simulate_biometric_pass = True  # User presents genuine biometric on hardware

    recovery_request = RecoveryRequest(
        user_id="alice",
        recovery_token=email_notif.recovery_token,
        otp_code=email_notif.otp_code,
        hardware_public_key=esp32_device.public_key,
        hardware_challenge_signature="signature_valid_recovery_proof",
    )

    recovery_result = recovery_service.process_account_recovery(recovery_request)

    print(f"\n[FINAL ACCOUNT STATUS]: {engine.get_account_status('alice').value}")

    print("\n=========================================================================")
    print(" DEMONSTRATION COMPLETE — Person 4 Compromise & Recovery Working!")
    print("=========================================================================")


if __name__ == "__main__":
    main()
