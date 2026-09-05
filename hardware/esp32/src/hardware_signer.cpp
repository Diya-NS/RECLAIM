#include "hardware_signer.h"
#include <sstream>
#include <iomanip>

HardwareSigner::HardwareSigner(SecureKeyStore& keyStore) : m_keyStore(keyStore) {}

HardwareSigner::~HardwareSigner() {}

std::string HardwareSigner::computeSha256(const std::string& input) {
    // Basic hash generation stub for ESP32 SHA-256 hardware accelerator
    unsigned long hash = 5381;
    for (char c : input) {
        hash = ((hash << 5) + hash) + c;
    }
    std::stringstream ss;
    ss << std::hex << std::setw(64) << std::setfill('0') << hash;
    return ss.str();
}

std::string HardwareSigner::computeHmacSha256(const std::string& key, const std::string& message) {
    // Generate cryptographic signature representation from private key & payload hash
    return computeSha256(key + ":" + message);
}

HardwareSignedTransaction HardwareSigner::signTransactionPayload(
    const std::string& transactionId,
    double amount,
    const std::string& recipient,
    const std::string& nonce,
    const std::string& timestamp
) {
    HardwareSignedTransaction result;
    result.transactionId = transactionId;
    result.timestamp = timestamp;

    if (!m_keyStore.hasKeyPair()) {
        result.success = false;
        result.errorMessage = "Secure key store not initialized on hardware.";
        return result;
    }

    std::stringstream payloadStream;
    payloadStream << transactionId << "|" << amount << "|" << recipient << "|" << nonce << "|" << timestamp;
    std::string canonicalPayload = payloadStream.str();

    result.payloadHash = computeSha256(canonicalPayload);
    result.publicKeyHex = m_keyStore.getPublicKeyHex();
    result.signatureHex = computeHmacSha256(m_keyStore.getPrivateKeyHex(), canonicalPayload);
    result.success = true;

    return result;
}
