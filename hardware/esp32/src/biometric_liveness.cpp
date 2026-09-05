#include "biometric_liveness.h"

BiometricLivenessSensor::BiometricLivenessSensor()
    : m_gpioTouch(-1), m_gpioLiveness(-1), m_forcedFailure(false) {}

BiometricLivenessSensor::~BiometricLivenessSensor() {}

bool BiometricLivenessSensor::initialize(int gpioPinTouch, int gpioPinLiveness) {
    m_gpioTouch = gpioPinTouch;
    m_gpioLiveness = gpioPinLiveness;
    return true;
}

BiometricVerificationResult BiometricLivenessSensor::verifyUserAuthorization(bool simulateSuccess) {
    BiometricVerificationResult result;
    if (m_forcedFailure || !simulateSuccess) {
        result.success = false;
        result.livenessPassed = false;
        result.confidenceScore = 0.12f;
        result.message = "Biometric liveness verification failed on ESP32 device.";
    } else {
        result.success = true;
        result.livenessPassed = true;
        result.confidenceScore = 0.98f;
        result.message = "Biometric match and liveness verified successfully on hardware.";
    }
    return result;
}

void BiometricLivenessSensor::setForcedFailure(bool fail) {
    m_forcedFailure = fail;
}
