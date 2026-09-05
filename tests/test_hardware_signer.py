"""
Unit Tests for ESP32 Hardware Device & Signer
Person 3: Hardware responsibility
"""

import unittest
import hashlib
from hardware.simulator.esp32_simulator import ESP32DeviceHardware


class TestESP32HardwareSigner(unittest.TestCase):

    def test_esp32_hardware_initialization(self):
        device = ESP32DeviceHardware(device_id="TEST-ESP32-01")
        status = device.get_status()
        
        self.assertEqual(status["device_id"], "TEST-ESP32-01")
        self.assertTrue(status["public_key"].startswith("04"))
        self.assertEqual(status["hardware_enclave_status"], "LOCKED_AND_SECURE")

    def test_esp32_valid_transaction_signing(self):
        device = ESP32DeviceHardware()
        tx_data = {
            "transaction_id": "TX-1001",
            "amount": 2500.0,
            "recipient": "acc_receiver_88",
            "nonce": "n_abc123",
            "timestamp": "2026-09-05T22:00:00Z",
        }

        result = device.sign_transaction(tx_data)

        self.assertTrue(result["success"])
        self.assertEqual(result["transaction_id"], "TX-1001")
        self.assertIsNotNone(result["signature"])
        self.assertEqual(result["public_key"], device.public_key)
        self.assertTrue(result["biometric_verified"])
        self.assertTrue(result["liveness_verified"])

    def test_esp32_biometric_failure_prevents_signing(self):
        device = ESP32DeviceHardware()
        device.simulate_biometric_pass = False  # Simulate fingerprint mismatch

        tx_data = {
            "transaction_id": "TX-1002",
            "amount": 10000.0,
            "recipient": "acc_evil_hacker",
            "nonce": "n_xyz456",
            "timestamp": "2026-09-05T22:05:00Z",
        }

        result = device.sign_transaction(tx_data)

        self.assertFalse(result["success"])
        self.assertIsNone(result["signature"])
        self.assertFalse(result["biometric_verified"])
        self.assertIn("Biometric fingerprint mismatch", result["error"])

    def test_esp32_liveness_failure_prevents_signing(self):
        device = ESP32DeviceHardware()
        device.simulate_liveness_pass = False  # Simulate biometric spoofing attack

        tx_data = {
            "transaction_id": "TX-1003",
            "amount": 50000.0,
            "recipient": "acc_unknown",
            "nonce": "n_789101",
            "timestamp": "2026-09-05T22:10:00Z",
        }

        result = device.sign_transaction(tx_data)

        self.assertFalse(result["success"])
        self.assertIsNone(result["signature"])
        self.assertFalse(result["liveness_verified"])
        self.assertIn("Liveness verification failed", result["error"])


if __name__ == "__main__":
    unittest.main()
