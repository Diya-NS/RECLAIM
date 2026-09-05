"""
Unit & Integration Tests for Person 4: Compromise, Freeze & Recovery Subsystem
"""

import unittest
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
from src.compromise_recovery import (
    AccountStatus,
    FreezeReason,
    CompromiseEngine,
    NotificationDispatcher,
    RecoveryService,
    RecoveryRequest,
)


class TestCompromiseRecoverySubsystem(unittest.TestCase):

    def setUp(self):
        self.dispatcher = NotificationDispatcher()
        self.engine = CompromiseEngine(notification_dispatcher=self.dispatcher)
        self.recovery = RecoveryService(compromise_engine=self.engine)
        
        self.device = ESP32DeviceHardware(device_id="TEST-ESP32-NODE")
        self.client = HardwareClient(direct_hardware_device=self.device)
        self.verifier = SignatureVerifier()
        self.verifier.register_trusted_device_key(self.device.public_key)

        # Wire Person 4's callback into Person 3's service
        self.hw_service = HardwareAuthorizationService(
            hardware_client=self.client,
            signature_verifier=self.verifier,
            person4_compromise_handler=self.engine.handle_person3_hardware_failure_event,
            max_allowed_failed_attempts=3,
        )

    def test_freeze_account_and_audit_logging(self):
        event = self.engine.freeze_account(
            user_id="alice",
            reason=FreezeReason.MAX_HARDWARE_FAILS_EXCEEDED,
            associated_tx_id="TX-FAIL-100",
            risk_factors=["amount_exceeded"],
        )

        self.assertEqual(self.engine.get_account_status("alice"), AccountStatus.FROZEN)
        self.assertEqual(event.user_id, "alice")
        self.assertEqual(event.reason, FreezeReason.MAX_HARDWARE_FAILS_EXCEEDED)
        self.assertEqual(len(self.engine.audit_log), 1)

    def test_emergency_notification_dispatch(self):
        event = self.engine.freeze_account(
            user_id="bob",
            reason=FreezeReason.UNAUTHORIZED_BIOMETRIC,
            associated_tx_id="TX-FAIL-200",
        )

        self.assertEqual(len(self.dispatcher.dispatched_notifications), 2)
        email_notif = [n for n in self.dispatcher.dispatched_notifications if n.channel == "EMAIL"][0]
        sms_notif = [n for n in self.dispatcher.dispatched_notifications if n.channel == "SMS"][0]

        self.assertIn("bob", email_notif.user_id)
        self.assertEqual(len(sms_notif.otp_code), 6)
        self.assertTrue(sms_notif.recovery_token.startswith("REC-TOKEN-"))

    def test_recovery_fails_with_invalid_otp(self):
        event = self.engine.freeze_account(
            user_id="alice",
            reason=FreezeReason.MAX_HARDWARE_FAILS_EXCEEDED,
        )
        notif = self.dispatcher.dispatched_notifications[0]

        req = RecoveryRequest(
            user_id="alice",
            recovery_token=notif.recovery_token,
            otp_code="000000",  # WRONG OTP
            hardware_public_key=self.device.public_key,
            hardware_challenge_signature="sig_123",
        )

        res = self.recovery.process_account_recovery(req)

        self.assertFalse(res.success)
        self.assertEqual(res.status, AccountStatus.FROZEN)
        self.assertEqual(res.error, "INVALID_RECOVERY_OTP")

    def test_successful_multi_factor_account_recovery(self):
        # 1. Freeze account
        event = self.engine.freeze_account(
            user_id="alice",
            reason=FreezeReason.MAX_HARDWARE_FAILS_EXCEEDED,
        )
        notif = self.dispatcher.dispatched_notifications[0]

        # 2. Submit valid recovery request with Token + OTP + Hardware Proof
        req = RecoveryRequest(
            user_id="alice",
            recovery_token=notif.recovery_token,
            otp_code=notif.otp_code,  # VALID OTP
            hardware_public_key=self.device.public_key,
            hardware_challenge_signature="valid_sig_proof",
        )

        res = self.recovery.process_account_recovery(req)

        self.assertTrue(res.success)
        self.assertEqual(res.status, AccountStatus.ACTIVE)
        self.assertEqual(self.engine.get_account_status("alice"), AccountStatus.ACTIVE)

    def test_full_end_to_end_person2_person3_person4_flow(self):
        # Disable biometric on ESP32 device to simulate attacks
        self.device.simulate_biometric_pass = False

        # Person 2 sends 3 consecutive TRIGGER_RECLAIM requests
        for i in range(1, 4):
            tx = TransactionPayload(
                transaction_id=f"TX-ATTACK-{i}",
                amount=25000.0,
                recipient="hacker_vault",
                sender="attacker_bob",
                risk_level=RiskLevel.HIGH,
                risk_score=0.95,
                timestamp="2026-09-06T00:00:00Z",
                nonce=f"nonce_attack_{i}",
                risk_decision=RiskDecision.TRIGGER_RECLAIM.value,
            )
            res = self.hw_service.process_transaction_authorization(tx)

        # Verify Person 4's CompromiseEngine froze the account automatically!
        self.assertEqual(self.engine.get_account_status("attacker_bob"), AccountStatus.FROZEN)
        
        # Verify notifications were dispatched
        bob_notifs = [n for n in self.dispatcher.dispatched_notifications if n.user_id == "attacker_bob"]
        self.assertGreaterEqual(len(bob_notifs), 2)
        recovery_token = bob_notifs[0].recovery_token
        otp_code = bob_notifs[0].otp_code

        # Re-enable biometric on ESP32 for valid recovery
        self.device.simulate_biometric_pass = True

        # Unfreeze account via Person 4 Recovery Service
        rec_req = RecoveryRequest(
            user_id="attacker_bob",
            recovery_token=recovery_token,
            otp_code=otp_code,
            hardware_public_key=self.device.public_key,
            hardware_challenge_signature="valid_hw_proof",
        )
        rec_res = self.recovery.process_account_recovery(rec_req)

        self.assertTrue(rec_res.success)
        self.assertEqual(rec_res.status, AccountStatus.ACTIVE)
        self.assertEqual(self.engine.get_account_status("attacker_bob"), AccountStatus.ACTIVE)


if __name__ == "__main__":
    unittest.main()
