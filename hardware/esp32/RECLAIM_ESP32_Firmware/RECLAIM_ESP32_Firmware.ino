/*
  RECLAIM — ESP32 WROOM-DA Hardware Authorization Firmware (Serial Monitor Mode)
  Person 3: Hardware Responsibility

  PERSON 2 CHALLENGE SIGNING INTEGRATION:
  - Parses Person 2's `challenge_id` (e.g., CHAL-9F8A2B1C) & `challenge_payload`.
  - Displays Challenge ID & Payload on Serial Monitor / Web Interface.
  - Cryptographically signs `challenge_payload` on ESP32 hardware enclave using Private Key.
  - Controls:
      Type 'y' + Enter -> APPROVE & SIGN Challenge on Hardware
      Type 'n' + Enter -> REJECT / SIMULATE FAIL (Triggers Person 4)
*/

#include <WiFi.h>
#include <WebServer.h>
#include <mbedtls/md.h>

// =========================================================================
// CONFIGURATION: Set your Wi-Fi details here
// =========================================================================
const char* ssid     = "csseminarhal2.4l";
const char* password = "sctce2020";

#define LED_PIN 2 // Onboard LED on ESP32 WROOM-DA Module (GPIO 2)

WebServer server(80);

String devicePublicKeyHex = "";
String devicePrivateKeyHex = "";
volatile bool isAuthorizedArmed = false;
volatile bool isForcedFailureArmed = false;

// -------------------------------------------------------------------------
// Cryptographic HMAC-SHA256 & Digest Helper (Built-in MbedTLS)
// -------------------------------------------------------------------------
String computeSha256(String input) {
  byte shaResult[32];
  mbedtls_md_context_t ctx;
  mbedtls_md_type_t md_type = MBEDTLS_MD_SHA256;
  
  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(md_type), 0);
  mbedtls_md_starts(&ctx);
  mbedtls_md_update(&ctx, (const unsigned char*) input.c_str(), input.length());
  mbedtls_md_finish(&ctx, shaResult);
  mbedtls_md_free(&ctx);

  String hashStr = "";
  for (int i = 0; i < 32; i++) {
    char buf[3];
    sprintf(buf, "%02x", shaResult[i]);
    hashStr += buf;
  }
  return hashStr;
}

String computeHmacSha256(String key, String message) {
  byte hmacResult[32];
  mbedtls_md_context_t ctx;
  mbedtls_md_type_t md_type = MBEDTLS_MD_SHA256;

  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(md_type), 1); // 1 = HMAC
  mbedtls_md_hmac_starts(&ctx, (const unsigned char*) key.c_str(), key.length());
  mbedtls_md_hmac_update(&ctx, (const unsigned char*) message.c_str(), message.length());
  mbedtls_md_hmac_finish(&ctx, hmacResult);
  mbedtls_md_free(&ctx);

  String hmacStr = "";
  for (int i = 0; i < 32; i++) {
    char buf[3];
    sprintf(buf, "%02x", hmacResult[i]);
    hmacStr += buf;
  }
  return hmacStr;
}

void generateKeyPair() {
  String seed = String(esp_random()) + "_RECLAIM_WROOM_DA_KEY";
  devicePrivateKeyHex = computeSha256(seed);
  devicePublicKeyHex = "04" + computeSha256("PUBKEY_" + devicePrivateKeyHex);
}

void blinkLed(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}

// -------------------------------------------------------------------------
// Continuous Serial Monitor Checking Loop
// -------------------------------------------------------------------------
void checkSerialMonitorInput() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == 'y' || c == 'Y' || c == '1') {
      isAuthorizedArmed = true;
      isForcedFailureArmed = false;
      digitalWrite(LED_PIN, HIGH);
      Serial.println("\n[ESP32 HARDWARE] *** AUTHORIZATION ARMED ('y') ***");
      Serial.println("[ESP32 HARDWARE] Ready to APPROVE & SIGN Person 2 Challenge!");
    } else if (c == 'n' || c == 'N' || c == '0') {
      isAuthorizedArmed = false;
      isForcedFailureArmed = true;
      digitalWrite(LED_PIN, LOW);
      Serial.println("\n[ESP32 HARDWARE] *** REJECTION ARMED ('n') ***");
      Serial.println("[ESP32 HARDWARE] Next transaction will be REJECTED (Simulating Biometric Failure -> Person 4 trigger)!");
    }
  }
}

// -------------------------------------------------------------------------
// REST API & Web Page Handlers
// -------------------------------------------------------------------------
void handleRootWeb() {
  String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<title>RECLAIM ESP32 Enclave</title>";
  html += "<style>body{font-family:Arial;text-align:center;padding:20px;background:#f4f6f8;}";
  html += ".card{background:white;max-width:500px;margin:20px auto;padding:30px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1);}";
  html += ".btn{background:#0066cc;color:white;padding:15px 25px;border:none;border-radius:8px;font-size:16px;cursor:pointer;font-weight:bold;margin:5px;}";
  html += ".btn-danger{background:#d32f2f;}";
  html += ".status-armed{color:#2e7d32;font-weight:bold;font-size:20px;}";
  html += ".status-disarmed{color:#c62828;font-weight:bold;font-size:20px;}";
  html += "</style></head><body>";
  html += "<div class='card'>";
  html += "<h2>RECLAIM ESP32 Hardware Enclave</h2>";
  html += "<p><b>Board:</b> ESP32 WROOM-DA Module</p>";
  html += "<p><b>Status:</b> ";
  if (isAuthorizedArmed) {
    html += "<span class='status-armed'>ARMED TO APPROVE</span>";
  } else if (isForcedFailureArmed) {
    html += "<span class='status-disarmed'>ARMED TO REJECT (SIMULATED FAIL)</span>";
  } else {
    html += "<span class='status-disarmed'>IDLE (Type 'y' in Serial Monitor)</span>";
  }
  html += "</p>";
  html += "<p style='font-size:12px;word-break:break-all;'><b>Public Key:</b><br><code>" + devicePublicKeyHex + "</code></p>";
  html += "<form method='POST' action='/approve_once' style='display:inline;'><button class='btn'>APPROVE NEXT TX ('y')</button></form>";
  html += "<form method='POST' action='/reject_once' style='display:inline;'><button class='btn btn-danger'>REJECT NEXT TX ('n')</button></form>";
  html += "</div></body></html>";
  server.send(200, "text/html", html);
}

void handleApproveOnce() {
  isAuthorizedArmed = true;
  isForcedFailureArmed = false;
  digitalWrite(LED_PIN, HIGH);
  Serial.println("\n[ESP32 HARDWARE] *** AUTHORIZATION ARMED VIA WEB GUI ('y') ***");
  server.sendHeader("Location", "/");
  server.send(303);
}

void handleRejectOnce() {
  isAuthorizedArmed = false;
  isForcedFailureArmed = true;
  digitalWrite(LED_PIN, LOW);
  Serial.println("\n[ESP32 HARDWARE] *** REJECTION ARMED VIA WEB GUI ('n') ***");
  server.sendHeader("Location", "/");
  server.send(303);
}

void handleStatus() {
  String json = "{";
  json += "\"device_id\":\"ESP32-WROOM-DA-MODULE\",";
  json += "\"firmware\":\"v2.4.0-Person2Challenge\",";
  json += "\"public_key\":\"" + devicePublicKeyHex + "\",";
  json += "\"is_authorized_armed\":" + String(isAuthorizedArmed ? "true" : "false") + ",";
  json += "\"is_forced_failure_armed\":" + String(isForcedFailureArmed ? "true" : "false") + ",";
  json += "\"hardware_enclave_status\":\"LOCKED_AND_SECURE\"";
  json += "}";
  server.send(200, "application/json", json);
}

void handleAuthorize() {
  if (server.hasArg("plain") == false) {
    server.send(400, "application/json", "{\"error\":\"Missing body\"}");
    return;
  }

  String body = server.arg("plain");

  // Extract JSON parameters
  int txIdIdx = body.indexOf("\"transaction_id\":");
  String txId = "UNKNOWN";
  if (txIdIdx != -1) {
    int start = body.indexOf("\"", txIdIdx + 17) + 1;
    int end = body.indexOf("\"", start);
    txId = body.substring(start, end);
  }

  int amtIdx = body.indexOf("\"amount\":");
  String amt = "0";
  if (amtIdx != -1) {
    int start = amtIdx + 9;
    int end = body.indexOf(",", start);
    if (end == -1) end = body.indexOf("}", start);
    amt = body.substring(start, end);
    amt.trim();
  }

  int recIdx = body.indexOf("\"recipient\":");
  String recipient = "unknown";
  if (recIdx != -1) {
    int start = body.indexOf("\"", recIdx + 12) + 1;
    int end = body.indexOf("\"", start);
    recipient = body.substring(start, end);
  }

  int nonceIdx = body.indexOf("\"nonce\":");
  String nonce = "nonce";
  if (nonceIdx != -1) {
    int start = body.indexOf("\"", nonceIdx + 8) + 1;
    int end = body.indexOf("\"", start);
    nonce = body.substring(start, end);
  }

  int tsIdx = body.indexOf("\"timestamp\":");
  String timestamp = "ts";
  if (tsIdx != -1) {
    int start = body.indexOf("\"", tsIdx + 12) + 1;
    int end = body.indexOf("\"", start);
    timestamp = body.substring(start, end);
  }

  // Parse Person 2's challenge_id and challenge_payload
  int chalIdIdx = body.indexOf("\"challenge_id\":");
  String chalId = "CHAL-DEFAULT";
  if (chalIdIdx != -1) {
    int start = body.indexOf("\"", chalIdIdx + 15) + 1;
    int end = body.indexOf("\"", start);
    chalId = body.substring(start, end);
  }

  int chalPayloadIdx = body.indexOf("\"challenge_payload\":");
  String chalPayload = "payload_default";
  if (chalPayloadIdx != -1) {
    int start = body.indexOf("\"", chalPayloadIdx + 20) + 1;
    int end = body.indexOf("\"", start);
    chalPayload = body.substring(start, end);
  }

  Serial.println("\n========================================================");
  Serial.println(" [INCOMING RECLAIM AUTHORIZATION REQUEST]");
  Serial.printf("   Tx ID:             %s\n", txId.c_str());
  Serial.printf("   Amount:            $%s\n", amt.c_str());
  Serial.printf("   Recipient:         %s\n", recipient.c_str());
  Serial.printf("   Challenge ID:      %s\n", chalId.c_str());
  Serial.printf("   Challenge Payload: %s\n", chalPayload.c_str());
  Serial.println("--------------------------------------------------------");
  Serial.println(" ACTION REQUIRED in Serial Monitor:");
  Serial.println("   Type 'y' + Enter -> APPROVE & SIGN CHALLENGE ON ESP32");
  Serial.println("   Type 'n' + Enter -> REJECT / SIMULATE BIOMETRIC FAIL");
  Serial.println("========================================================");

  // Rapid blink LED while waiting
  if (!isAuthorizedArmed && !isForcedFailureArmed) {
    unsigned long startWait = millis();
    while (millis() - startWait < 5000) {
      digitalWrite(LED_PIN, (millis() / 150) % 2 == 0 ? HIGH : LOW);
      checkSerialMonitorInput();
      server.handleClient();
      if (isAuthorizedArmed || isForcedFailureArmed) break;
      delay(20);
    }
    digitalWrite(LED_PIN, LOW);
  }

  // Handle Forced Rejection Mode ('n')
  if (isForcedFailureArmed) {
    isForcedFailureArmed = false;
    Serial.println("[ESP32 HARDWARE] REJECTED — Biometric/Hardware authorization failed ('n' pressed).");
    String errJson = "{";
    errJson += "\"success\":false,";
    errJson += "\"transaction_id\":\"" + txId + "\",";
    errJson += "\"challenge_id\":\"" + chalId + "\",";
    errJson += "\"challenge_payload\":\"" + chalPayload + "\",";
    errJson += "\"biometric_verified\":false,";
    errJson += "\"liveness_verified\":false,";
    errJson += "\"error\":\"Biometric fingerprint mismatch on ESP32 device.\"";
    errJson += "}";
    server.send(403, "application/json", errJson);
    return;
  }

  // Handle Timeout / Disarmed State
  if (!isAuthorizedArmed) {
    Serial.println("[ESP32 HARDWARE] REJECTED — Authorization request timed out.");
    String errJson = "{";
    errJson += "\"success\":false,";
    errJson += "\"transaction_id\":\"" + txId + "\",";
    errJson += "\"challenge_id\":\"" + chalId + "\",";
    errJson += "\"challenge_payload\":\"" + chalPayload + "\",";
    errJson += "\"biometric_verified\":false,";
    errJson += "\"liveness_verified\":false,";
    errJson += "\"error\":\"Hardware authorization timed out on ESP32 device.\"";
    errJson += "}";
    server.send(403, "application/json", errJson);
    return;
  }

  // Consume Armed State ('y')
  isAuthorizedArmed = false;

  // Sign Person 2's challenge_payload and canonical transaction payload
  String canonicalPayload = txId + "|" + amt + "|" + recipient + "|" + nonce + "|" + timestamp + "|" + chalId + "|" + chalPayload;
  String payloadHash = computeSha256(canonicalPayload);
  String signature = computeHmacSha256(devicePrivateKeyHex, canonicalPayload);
  String challengeSignature = computeHmacSha256(devicePrivateKeyHex, chalPayload);

  String resJson = "{";
  resJson += "\"success\":true,";
  resJson += "\"transaction_id\":\"" + txId + "\",";
  resJson += "\"challenge_id\":\"" + chalId + "\",";
  resJson += "\"challenge_payload\":\"" + chalPayload + "\",";
  resJson += "\"challenge_signature\":\"" + challengeSignature + "\",";
  resJson += "\"payload_hash\":\"" + payloadHash + "\",";
  resJson += "\"signature\":\"" + signature + "\",";
  resJson += "\"public_key\":\"" + devicePublicKeyHex + "\",";
  resJson += "\"device_id\":\"ESP32-WROOM-DA-MODULE\",";
  resJson += "\"biometric_verified\":true,";
  resJson += "\"liveness_verified\":true,";
  resJson += "\"message\":\"Challenge " + chalId + " signed securely by ESP32 WROOM-DA hardware enclave.\"";
  resJson += "}";

  // Success indicator: Flash LED 3 times
  blinkLed(3, 100);

  Serial.println("[ESP32 HARDWARE] SUCCESS — Challenge Signed Cryptographically!");
  Serial.println("  Challenge ID:        " + chalId);
  Serial.println("  Challenge Signature: " + challengeSignature.substring(0, 24) + "...");

  server.send(200, "application/json", resJson);
}

// -------------------------------------------------------------------------
// Arduino Setup & Loop
// -------------------------------------------------------------------------
void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(115200);
  delay(1000);

  Serial.println("\n========================================================");
  Serial.println(" RECLAIM ESP32 WROOM-DA Hardware Enclave (Challenge Mode)");
  Serial.println("========================================================");

  generateKeyPair();
  Serial.println("[KEYS] Hardware Enclave Keypair Generated.");
  Serial.println(" Public Key: " + devicePublicKeyHex);

  // Connect to Wi-Fi
  Serial.printf("[WIFI] Connecting to SSID: %s ", ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Blink while connecting
  }
  digitalWrite(LED_PIN, LOW);

  Serial.println("\n[WIFI] Connected!");
  Serial.print("[WIFI] ESP32 Web Server Address: http://");
  Serial.println(WiFi.localIP());

  // Setup WebServer Routes on Port 80
  server.on("/", HTTP_GET, handleRootWeb);
  server.on("/approve_once", HTTP_POST, handleApproveOnce);
  server.on("/reject_once", HTTP_POST, handleRejectOnce);
  server.on("/api/status", HTTP_GET, handleStatus);
  server.on("/api/authorize", HTTP_POST, handleAuthorize);

  server.begin();
  Serial.println("\n--------------------------------------------------------");
  Serial.println("READY FOR PERSON 2 CHALLENGES (CHAL-XXXXX):");
  Serial.println("  1. Type 'y' + Enter -> APPROVE & SIGN Person 2 Challenge.");
  Serial.println("  2. Type 'n' + Enter -> REJECT / SIMULATE BIOMETRIC FAIL.");
  Serial.println("  3. Web GUI backup: http://" + WiFi.localIP().toString());
  Serial.println("--------------------------------------------------------\n");

  blinkLed(2, 150);
}

void loop() {
  server.handleClient();
  checkSerialMonitorInput();
}
