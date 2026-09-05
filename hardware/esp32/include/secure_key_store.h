#ifndef SECURE_KEY_STORE_H
#ifndef SECURE_KEY_STORE_H
#define SECURE_KEY_STORE_H

#include <string>
#include <vector>

/**
 * @brief Secure Key Store interface for ESP32 hardware enclave / NVS storage.
 * Manages asymmetric ECC key generation, secure storage, and retrieval on hardware.
 */
class SecureKeyStore {
public:
    SecureKeyStore();
    ~SecureKeyStore();

    bool initialize();
    bool hasKeyPair() const;
    bool generateKeyPair();
    std::string getPublicKeyHex() const;
    std::string getPrivateKeyHex() const;

private:
    bool m_initialized;
    std::string m_publicKeyHex;
    std::string m_privateKeyHex;

    void loadOrGenerate();
};

#endif // SECURE_KEY_STORE_H
