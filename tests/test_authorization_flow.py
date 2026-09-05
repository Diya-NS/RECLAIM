"""
Integration Tests for Hardware Authorization Service & Flow
Person 3: Hardware responsibility
Testing Person 2 (TRIGGER_RECLAIM) and Person 4 (3-Strike Freeze Mode)
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


class TestHardwareAuthorizationFlow(unittest.TestCase):

    def setUp(self):
        self.device = ESP32DeviceHardware(device_id="TEST-HARDWARE-NODE")
        self.client = HardwareClient(direct_hardware_device=self.device)
        self.verifier = SignatureVerifier()
        self.verifier.register_trusted_device_key(self.device.public_key)
        
        self.compromise_events = []
        def person4_handler(tx, ver_res):
            self.compromise_events.append((tx, ver_res))

        self.service = HardwareAuthorizationService(
            hardware_client=self.client,
            signature_verifier=self.verifier,
            person4_compromise_handler=person4_handler,
            max_allowed_failed_attempts=3,
        )

    def test_person2_trigger_reclaim_approved(self):
        tx = TransactionPayload(
            transaction_id="TX-RECLAIM-01",
            amount=15000.0,
            recipient="protected_reserve_vault",
            sender="alice",
            risk_level=RiskLevel.HIGH,
            risk_score=0.92,
            timestamp="2026-09-05T22:00:00Z",
            nonce="nonce_reclaim_01",
            risk_decision=RiskDecision.TRIGGER_RECLAIM.value,
            risk_factors=["amount_exceeded", "protected_reserve_accessed"],
        )

        res = self.service.process_transaction_authorization(tx)

        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, AuthorizationStatus.APPROVED)
        self.assertEqual(res.failed_attempts_count, 0)
        self.assertEqual(len(self.compromise_events), 0)

    def test_three_failed_attempts_triggers_person4_freeze_mode(self):
        self.device.simulate_biometric_pass = False  # Simulate biometric fail

        # Attempt 1
        tx1 = TransactionPayload(
            transaction_id="TX-FAIL-1",
            amount=50000.0,
            recipient="vault",
            sender="bob",
            risk_level=RiskLevel.HIGH,
            risk_score=0.95,
            timestamp="2026-09-05T22:01:00Z",
            nonce="nonce_fail_1",
            risk_decision=RiskDecision.TRIGGER_RECLAIM.value,
            risk_factors=["unrecognized_device"],
        )
        res1 = self.service.process_transaction_authorization(tx1)
        self.assertFalse(res1.is_valid)
        self.assertEqual(res1.status, AuthorizationStatus.BLOCKED)
        self.assertEqual(res1.failed_attempts_count, 1)
        self.assertEqual(len(self.compromise_events), 0)  # Not frozen yet at 1

        # Attempt 2
        tx2 = TransactionPayload(
            transaction_id="TX-FAIL-2",
            amount=50000.0,
            recipient="vault",
            sender="bob",
            risk_level=RiskLevel.HIGH,
            risk_score=0.95,
            timestamp="2026-09-05T22:02:00Z",
            nonce="nonce_fail_2",
            risk_decision=RiskDecision.TRIGGER_RECLAIM.value,
            risk_factors=["unrecognized_device"],
        )
        res2 = self.service.process_transaction_authorization(tx2)
        self.assertFalse(res2.is_valid)
        self.assertEqual(res2.status, AuthorizationStatus.BLOCKED)
        self.assertEqual(res2.failed_attempts_count, 2)
        self.assertEqual(len(self.compromise_events), 0)  # Not frozen yet at 2

        # Attempt 3 (STRIKE 3 -> FREEZE MODE!)
        tx3 = TransactionPayload(
            transaction_id="TX-FAIL-3",
            amount=50000.0,
            recipient="vault",
            sender="bob",
            risk_level=RiskLevel.HIGH,
            risk_score=0.95,
            timestamp="2026-09-05T22:03:00Z",
            nonce="nonce_fail_3",
            risk_decision=RiskDecision.TRIGGER_RECLAIM.value,
            risk_factors=["unrecognized_device"],
        )
        res3 = self.service.process_transaction_authorization(tx3)
        self.assertFalse(res3.is_valid)
        self.assertEqual(res3.status, AuthorizationStatus.FREEZE_MODE_TRIGGERED)
        self.assertEqual(res3.failed_attempts_count, 3)
        self.assertEqual(len(self.compromise_events), 1)  # Person 4 Freeze Mode Triggered!
        self.assertEqual(self.compromise_events[0][0].sender, "bob")

    def test_replay_attack_prevention(self):
        tx = TransactionPayload(
            transaction_id="TX-REPLAY-01",
            amount=5000.0,
            recipient="vendor",
            sender="charlie",
            risk_level=RiskLevel.HIGH,
            risk_score=0.88,
            timestamp="2026-09-05T22:00:00Z",
            nonce="nonce_reused_123",
            risk_decision=RiskDecision.TRIGGER_RECLAIM.value,
            risk_factors=["amount_exceeded"],
        )

        # First attempt succeeds
        res1 = self.service.process_transaction_authorization(tx)
        self.assertTrue(res1.is_valid)

        # Replay attempt fails
        res2 = self.service.process_transaction_authorization(tx)
        self.assertFalse(res2.is_valid)
        self.assertIn("Replay attack detected", res2.reason)


if __name__ == "__main__":
    unittest.main()
