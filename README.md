# RECLAIM — Hardware-Backed Authorization Subsystem

**Owner**: Person 3 (Hardware Responsibility)

This module implements hardware-backed transaction authorization for **RECLAIM**. When Person 2 (Risk System) flags a transaction as high-risk, Person 3's subsystem demands a cryptographic signature and biometric/liveness proof generated inside secure hardware (ESP32 / hardware enclave).

---

## 🔄 Transaction Flow

```
Person 2: "This transaction is high risk."
                 │
                 ▼
Person 3: "Prove authorization using the hardware."
                 │
  ┌──────────────┴──────────────┐
  ▼                             ▼
ESP32 Secure Hardware      Virtual ESP32 Simulator
(Biometric + ECC Sign)     (Local Server / Tests)
  │                             │
  └──────────────┬──────────────┘
                 │ Signed Payload & Liveness Proof
                 ▼
RECLAIM: Cryptographic Signature Verification
                 │
        ┌────────┴────────┐
        ▼                 ▼
     APPROVE           BLOCK ──► Person 4 (Compromise / Freeze / Recovery)
```

---

## 🛠 Features

1. **ESP32 Secure Hardware Firmware** (`hardware/esp32/`):
   - Secure Key Generation & NVS Storage.
   - Hardware Biometric & Liveness Sensor interface.
   - On-device cryptographic transaction signing.

2. **Virtual Hardware Simulator** (`hardware/simulator/esp32_simulator.py`):
   - Standalone Python HTTP server emulating ESP32 hardware enclave REST API.
   - Allows full local development and automated CI testing without physical hardware connected.

3. **RECLAIM Software Client & Verifier** (`src/hardware_auth/`):
   - `HardwareClient`: Connects to physical ESP32 or simulator over HTTP/REST.
   - `SignatureVerifier`: Validates SHA-256 / ECDSA signatures, enforces device public key whitelist, and prevents nonce replay attacks.
   - `HardwareAuthorizationService`: Coordinates Person 2 -> Person 3 -> Hardware -> Person 4 flow.

---

## 🚀 Running the Tests & Demo

### 1. Run Automated Test Suite
```bash
python -m pytest tests/
```

### 2. Run Interactive Flow Demonstration
```bash
python demo_flow.py
```

### 3. Run Virtual ESP32 Device Server Standalone
```bash
python hardware/simulator/esp32_simulator.py
```
- Endpoint Status: `http://127.0.0.1:8585/api/status`
- Endpoint Authorize: `POST http://127.0.0.1:8585/api/authorize`