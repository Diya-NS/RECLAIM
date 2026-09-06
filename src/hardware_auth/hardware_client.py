"""
Hardware Client Interface (ESP32 / Virtual Hardware Device)
Person 3: Hardware responsibility
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from .types import HardwareAuthRequest, HardwareAuthResponse


class HardwareClient:
    def __init__(self, endpoint_url: str = "http://127.0.0.1:8585", direct_hardware_device: Optional[Any] = None):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.direct_hardware_device = direct_hardware_device

    def get_device_status(self) -> Dict[str, Any]:
        if self.direct_hardware_device:
            return self.direct_hardware_device.get_status()
        
        url = f"{self.endpoint_url}/api/status"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RECLAIM-App/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": f"Failed to connect to hardware device at {url}: {str(e)}", "online": False}

    def request_hardware_signature(self, auth_req: HardwareAuthRequest) -> HardwareAuthResponse:
        payload_dict = {
            "transaction_id": auth_req.transaction_id,
            "amount": auth_req.amount,
            "recipient": auth_req.recipient,
            "nonce": auth_req.nonce,
            "timestamp": auth_req.timestamp,
            "challenge_id": auth_req.challenge_id,
            "challenge_payload": auth_req.challenge_payload,
        }

        if self.direct_hardware_device:
            raw_res = self.direct_hardware_device.sign_transaction(payload_dict)
            return HardwareAuthResponse(
                success=raw_res.get("success", False),
                transaction_id=raw_res.get("transaction_id", auth_req.transaction_id),
                challenge_id=raw_res.get("challenge_id", auth_req.challenge_id),
                challenge_payload=raw_res.get("challenge_payload", auth_req.challenge_payload),
                challenge_signature=raw_res.get("challenge_signature"),
                payload_hash=raw_res.get("payload_hash"),
                signature=raw_res.get("signature"),
                public_key=raw_res.get("public_key"),
                device_id=raw_res.get("device_id"),
                biometric_verified=raw_res.get("biometric_verified", False),
                liveness_verified=raw_res.get("liveness_verified", False),
                message=raw_res.get("message", ""),
                error=raw_res.get("error"),
            )

        url = f"{self.endpoint_url}/api/authorize"
        data_bytes = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "RECLAIM-App/1.0"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw_res = json.loads(resp.read().decode("utf-8"))
                return HardwareAuthResponse(
                    success=raw_res.get("success", False),
                    transaction_id=raw_res.get("transaction_id", auth_req.transaction_id),
                    challenge_id=raw_res.get("challenge_id", auth_req.challenge_id),
                    challenge_payload=raw_res.get("challenge_payload", auth_req.challenge_payload),
                    challenge_signature=raw_res.get("challenge_signature"),
                    payload_hash=raw_res.get("payload_hash"),
                    signature=raw_res.get("signature"),
                    public_key=raw_res.get("public_key"),
                    device_id=raw_res.get("device_id"),
                    biometric_verified=raw_res.get("biometric_verified", False),
                    liveness_verified=raw_res.get("liveness_verified", False),
                    message=raw_res.get("message", ""),
                    error=raw_res.get("error"),
                )
        except urllib.error.HTTPError as http_err:
            try:
                raw_res = json.loads(http_err.read().decode("utf-8"))
                return HardwareAuthResponse(
                    success=False,
                    transaction_id=auth_req.transaction_id,
                    challenge_id=auth_req.challenge_id,
                    challenge_payload=auth_req.challenge_payload,
                    error=raw_res.get("error", f"HTTP {http_err.code}"),
                    message=raw_res.get("message", "Hardware transaction authorization rejected."),
                )
            except Exception:
                return HardwareAuthResponse(
                    success=False,
                    transaction_id=auth_req.transaction_id,
                    challenge_id=auth_req.challenge_id,
                    challenge_payload=auth_req.challenge_payload,
                    error=f"HTTP {http_err.code}: Hardware error",
                )
        except Exception as e:
            return HardwareAuthResponse(
                success=False,
                transaction_id=auth_req.transaction_id,
                challenge_id=auth_req.challenge_id,
                challenge_payload=auth_req.challenge_payload,
                error=f"Communication failure with hardware device: {str(e)}",
            )
