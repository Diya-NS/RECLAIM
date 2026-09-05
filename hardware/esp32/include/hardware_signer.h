#ifndef HARDWARE_SIGNER_H
#define HARDWARE_SIGNER_H

#include <string>
#include "secure_key_store.h"

struct HardwareSignedTransaction {
    bool success;
    std::string transactionId;
    std::string signatureHex;
    std::string publicKeyHex;
    std::string payloadHash;
    std::string timestamp;
    std::string errorMessage;
};

class HardwareSigner {
public:
    HardwareSigner(SecureKeyStore& keyStore);
    ~HardwareSigner();

    HardwareSignedTransaction signTransactionPayload(
        const std::string& transactionId,
        double amount,
        const std::string& recipient,
        const std::string& nonce,
        const std::string& timestamp
    );

private:
    SecureKeyStore& m_keyStore;
    std::string computeSha256(const std::string& input);
    std::string computeHmacSha256(const std::string& key, const std::string& message);
};

#endif // HARDWARE_SIGNER_H
