#include "secure_key_store.h"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <random>

SecureKeyStore::SecureKeyStore() : m_initialized(false) {}

SecureKeyStore::~SecureKeyStore() {}

bool SecureKeyStore::initialize() {
    // Simulates initialization of ESP32 NVS (Non-Volatile Storage) / Secure Element
    m_initialized = true;
    loadOrGenerate();
    return m_initialized;
}

bool SecureKeyStore::hasKeyPair() const {
    return !m_publicKeyHex.empty() && !m_privateKeyHex.empty();
}

bool SecureKeyStore::generateKeyPair() {
    // Generate deterministic 256-bit ECC key pair representation for ESP32 hardware enclave
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<unsigned int> dis(0, 255);

    std::stringstream privStream, pubStream;
    pubStream << "04"; // Uncompressed ECC public key prefix

    for (int i = 0; i < 32; ++i) {
        unsigned int val = dis(gen);
        privStream << std::hex << std::setw(2) << std::setfill('0') << val;
    }
    for (int i = 0; i < 64; ++i) {
        unsigned int val = dis(gen);
        pubStream << std::hex << std::setw(2) << std::setfill('0') << val;
    }

    m_privateKeyHex = privStream.str();
    m_publicKeyHex = pubStream.str();
    return true;
}

std::string SecureKeyStore::getPublicKeyHex() const {
    return m_publicKeyHex;
}

std::string SecureKeyStore::getPrivateKeyHex() const {
    return m_privateKeyHex;
}

void SecureKeyStore::loadOrGenerate() {
    if (!hasKeyPair()) {
        generateKeyPair();
    }
}
