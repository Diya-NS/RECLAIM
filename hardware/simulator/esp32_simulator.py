"""
ESP32 Hardware Authorization Device Simulator
Person 3: Hardware responsibility

Emulates physical ESP32 secure enclave hardware:
- Hardware-backed keypair generation and secure storage
- Challenge ID display & challenge_payload cryptographic signing
- Biometric sensor input & liveness verification
- On-device cryptographic transaction signing
- HTTP API interface for RECLAIM app/backend integration
"""

import hashlib
import hmac
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import threading
from typing import Dict, Any, Tuple


class ESP32DeviceHardware:
    """Virtual ESP32 Hardware Enclave Emulation"""

    def __init__(self, device_id: str = "ESP32-SECURE-NODE-01"):
        self.device_id = device_id
        self.firmware_version = "v2.4.0-RECLAIM-HW"
        self.biometric_sensor_active = True
        self.simulate_biometric_pass = True
        self.simulate_liveness_pass = True
        
        # Hardware keypair storage
        self._private_key = self._generate_hardware_seed()
        self.public_key = self._derive_public_key(self._private_key)

    def _generate_hardware_seed(self) -> bytes:
        """Simulate secure TRNG seed generation"""
        return hashlib.sha256(os.urandom(32) + b"RECLAIM_ESP32_SECURE_BOOT").digest()

    def _derive_public_key(self, private_key: bytes) -> str:
        """Derive hardware public key string"""
        pub_digest = hashlib.sha256(b"PUBKEY_PREFIX_04_" + private_key).hexdigest()
        return f"04{pub_digest}"

    def get_status(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "firmware": self.firmware_version,
            "public_key": self.public_key,
            "biometric_sensor_ok": self.biometric_sensor_active,
            "simulated_biometric_pass": self.simulate_biometric_pass,
            "simulated_liveness_pass": self.simulate_liveness_pass,
            "hardware_enclave_status": "LOCKED_AND_SECURE",
        }

    def verify_biometric_and_liveness(self) -> Tuple[bool, bool, str]:
        if not self.biometric_sensor_active:
            return False, False, "Biometric sensor hardware offline or disabled."
        if not self.simulate_biometric_pass:
            return False, False, "Biometric fingerprint mismatch on ESP32 device."
        if not self.simulate_liveness_pass:
            return True, False, "Liveness verification failed (possible spoof attempt detected)."
        return True, True, "Biometric and liveness successfully verified on ESP32."

    def sign_transaction(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes on-device cryptographic signing over Person 2's challenge_payload and transaction payload.
        """
        bio_ok, liveness_ok, bio_msg = self.verify_biometric_and_liveness()
        
        challenge_id = tx_data.get("challenge_id", "CHAL-9F8A2B1C")
        challenge_payload = tx_data.get("challenge_payload", "a7c3b2f901e4d812")

        if not bio_ok or not liveness_ok:
            return {
                "success": False,
                "error": bio_msg,
                "biometric_verified": bio_ok,
                "liveness_verified": liveness_ok,
                "transaction_id": tx_data.get("transaction_id", "UNKNOWN"),
                "challenge_id": challenge_id,
                "challenge_payload": challenge_payload,
                "challenge_signature": None,
                "signature": None,
                "public_key": self.public_key,
            }

        # Format canonical transaction payload: transaction_id|amount|recipient|nonce|timestamp|challenge_id|challenge_payload
        canonical_payload = (
            f"{tx_data.get('transaction_id')}|"
            f"{tx_data.get('amount')}|"
            f"{tx_data.get('recipient')}|"
            f"{tx_data.get('nonce')}|"
            f"{tx_data.get('timestamp')}|"
            f"{challenge_id}|"
            f"{challenge_payload}"
        )

        payload_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
        
        # 1. Sign canonical transaction payload
        signature = hmac.new(
            self._private_key,
            canonical_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        # 2. Sign Person 2's challenge_payload explicitly
        challenge_signature = hmac.new(
            self._private_key,
            challenge_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return {
            "success": True,
            "transaction_id": tx_data.get("transaction_id"),
            "challenge_id": challenge_id,
            "challenge_payload": challenge_payload,
            "challenge_signature": challenge_signature,
            "payload_hash": payload_hash,
            "signature": signature,
            "public_key": self.public_key,
            "device_id": self.device_id,
            "biometric_verified": True,
            "liveness_verified": True,
            "message": f"Challenge '{challenge_id}' and transaction payload signed securely by ESP32 hardware enclave.",
        }


# Global device instance for HTTP server mode
esp32_device = ESP32DeviceHardware()


class ESP32HTTPRequestHandler(BaseHTTPRequestHandler):
    def _send_response_json(self, status_code: int, data: Dict[str, Any]):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        if self.path == "/api/status":
            self._send_response_json(200, esp32_device.get_status())
        elif self.path == "/api/public_key":
            self._send_response_json(200, {"public_key": esp32_device.public_key})
        else:
            self._send_response_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            payload = {}

        if self.path == "/api/authorize":
            result = esp32_device.sign_transaction(payload)
            status_code = 200 if result.get("success") else 403
            self._send_response_json(status_code, result)
        elif self.path == "/api/configure_biometric":
            if "biometric_pass" in payload:
                esp32_device.simulate_biometric_pass = bool(payload["biometric_pass"])
            if "liveness_pass" in payload:
                esp32_device.simulate_liveness_pass = bool(payload["liveness_pass"])
            self._send_response_json(200, esp32_device.get_status())
        else:
            self._send_response_json(404, {"error": "Endpoint not found"})

    def log_message(self, format, *args):
        pass


def run_simulator_server(host: str = "127.0.0.1", port: int = 8585, blocking: bool = True):
    server = ThreadingHTTPServer((host, port), ESP32HTTPRequestHandler)
    print(f"[ESP32 SIMULATOR] Server running at http://{host}:{port}")
    if blocking:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[ESP32 SIMULATOR] Stopping server.")
            server.server_close()
    else:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server


if __name__ == "__main__":
    port = 8585
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_simulator_server(port=port, blocking=True)
