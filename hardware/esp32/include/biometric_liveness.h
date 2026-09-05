#ifndef BIOMETRIC_LIVENESS_H
#define BIOMETRIC_LIVENESS_H

#include <string>

struct BiometricVerificationResult {
    bool success;
    bool livenessPassed;
    float confidenceScore;
    std::string message;
};

class BiometricLivenessSensor {
public:
    BiometricLivenessSensor();
    ~BiometricLivenessSensor();

    bool initialize(int gpioPinTouch, int gpioPinLiveness);
    BiometricVerificationResult verifyUserAuthorization(bool simulateSuccess = true);
    void setForcedFailure(bool fail);

private:
    int m_gpioTouch;
    int m_gpioLiveness;
    bool m_forcedFailure;
};

#endif // BIOMETRIC_LIVENESS_H
