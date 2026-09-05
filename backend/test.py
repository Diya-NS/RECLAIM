import json
import requests

URL = "http://127.0.0.1:8000/api/v1/risk/evaluate"

print("\n--- TEST 1: Normal Safe Transaction (₹2,000 to Mom) ---")
payload_safe = {
    "user_id": "user_101",
    "amount": 2000,
    "recipient_id": "mom_axis_001",
    "device_id": "device_pixel8_abc",
}
res = requests.post(URL, json=payload_safe).json()
print(json.dumps(res, indent=2))

print(
    "\n--- TEST 2: Hack Demo Attempt (₹1,00,000 Transfer on Unknown Device) ---"
)
payload_hack = {
    "user_id": "user_101",
    "amount": 100000,
    "recipient_id": "hacker_unknown_acc",
    "device_id": "attacker_kali_vm",
}
res = requests.post(URL, json=payload_hack).json()
print(json.dumps(res, indent=2))