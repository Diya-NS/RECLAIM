/**
 * RECLAIM — Hardware-Backed Authorization Device Firmware (ESP32)
 * Person 3: Hardware Responsibility
 */

#include <iostream>
#include "secure_key_store.h"
#include "biometric_liveness.h"
#include "hardware_signer.h"

int main() {
    std::cout << "========================================================\n";
    std::cout << " RECLAIM ESP32 Hardware Authorization Subsystem\n";
    std::cout << "========================================================\n";

    SecureKeyStore keyStore;
    if (!keyStore.initialize()) {
        std::cerr << "[ERROR] Failed to initialize ESP32 Secure Key Store.\n";
        return 1;
    }
    std::cout << "[INFO] KeyStore ready. Public Key: " << keyStore.getPublicKeyHex().substr(0, 24) << "...\n";

    BiometricLivenessSensor bioSensor;
    bioSensor.initialize(4, 5);
    BiometricVerificationResult bioRes = bioSensor.verifyUserAuthorization(true);
    std::cout << "[INFO] Biometric check: " << bioRes.message << "\n";

    HardwareSigner signer(keyStore);
    HardwareSignedTransaction signedTx = signer.signTransactionPayload(
        "TX-998822", 15000.00, "recipient_account_xyz", "nonce_7711", "2026-09-05T22:00:00Z"
    );

    if (signedTx.success) {
        std::cout << "[SUCCESS] Transaction Signed on Hardware!\n";
        std::cout << "  Tx ID:     " << signedTx.transactionId << "\n";
        std::cout << "  Hash:      " << signedTx.payloadHash.substr(0, 32) << "...\n";
        std::cout << "  Signature: " << signedTx.signatureHex.substr(0, 32) << "...\n";
    } else {
        std::cerr << "[ERROR] Hardware signing failed: " << signedTx.errorMessage << "\n";
    }

    return 0;
}
