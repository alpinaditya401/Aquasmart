#include <esp_task_wdt.h>
#include <time.h>

#include "aqs_actuators.h"
#include "aqs_common.h"
#include "aqs_display.h"
#include "aqs_network.h"
#include "aqs_sensors.h"

uint32_t nextDisplay = 0, nextReport = 0;

void setup() {
  Serial.begin(115200);
  if (relayEnabled()) {
    digitalWrite(PIN_RELAY, RELAY_ACTIVE_LOW ? HIGH : LOW); pinMode(PIN_RELAY, OUTPUT);
  }
  if (pumpEnabled()) {
    digitalWrite(PIN_PUMP, PUMP_ACTIVE_LOW ? HIGH : LOW); pinMode(PIN_PUMP, OUTPUT);
  }
  if (ENABLE_FEEDER) { feeder.setPeriodHertz(50); feeder.attach(PIN_SERVO, 500, 2400); }
  safeOutputs();
  // The Arduino core already runs the task watchdog at 5 s, so init() would fail; reconfigure instead.
  esp_task_wdt_config_t watchdog = {.timeout_ms = 15000, .idle_core_mask = 0, .trigger_panic = true};
  esp_task_wdt_reconfigure(&watchdog); esp_task_wdt_add(nullptr);
  storageReady = journal.begin("aquasmart", false);
  String recovery = journal.getString("pending", ""); int delimiter = recovery.indexOf('|');
  if (delimiter == 32) { currentId = recovery.substring(0, delimiter); terminalStatus = recovery.substring(delimiter + 1); }
  configured = storageReady && String(WIFI_SSID) != "GANTI_SEBELUM_UPLOAD"
    && String(WIFI_PASSWORD) != "GANTI_SEBELUM_UPLOAD" && String(DEVICE_KEY) != "GANTI_SEBELUM_UPLOAD"
    && String(DEVICE_ID) != "GANTI_SEBELUM_UPLOAD" && String(API_BASE).indexOf("GANTI_SEBELUM_UPLOAD") < 0;
  if (String(API_BASE).startsWith("https://") && !DEVELOPMENT_INSECURE_TLS && String(ROOT_CA).indexOf("BEGIN CERTIFICATE") < 0) configured = false;
  if (DEVELOPMENT_INSECURE_TLS) Serial.println("PERINGATAN: verifikasi identitas TLS DIMATIKAN. Hanya untuk pengembangan, bukan bukti keamanan.");
  analogReadResolution(12);
  for (int i = 0; i < CH_COUNT; ++i) if (analogEnabled[i]) analogSetPinAttenuation(analogPins[i], ADC_11db);
  if (ULTRASONIC_WIRING_CONFIRMED) {
    pinMode(PIN_ULTRASONIC_TRIG, OUTPUT); digitalWrite(PIN_ULTRASONIC_TRIG, LOW);
    pinMode(PIN_ULTRASONIC_ECHO, INPUT);
  }
  if (DS18B20_WIRING_CONFIRMED) { thermometer.begin(); thermometer.setResolution(12); thermometer.setWaitForConversion(false); }
  if (ENABLE_LCD) {
    Wire.begin(PIN_LCD_SDA, PIN_LCD_SCL);
    lcd.init(); lcd.backlight();
    printLine(0, "AquaSmart"); printLine(1, "Menyalakan...");
  }
  sessionId = "esp32-" + String(uint32_t(ESP.getEfuseMac()), HEX) + "-" + String(esp_random(), HEX);
  WiFi.mode(WIFI_STA); WiFi.setAutoReconnect(false);
  offlineAt = millis();
  Serial.println(configured ? "Konfigurasi termuat, keluaran aman." : "Konfigurasi atau penyimpanan belum lengkap, keluaran dimatikan.");
}

void loop() {
  esp_task_wdt_reset(); uint32_t now = millis();
  // Sensors, LCD and Serial keep running without WiFi so wiring can be checked on the bench.
  sampleSensors(now);
  if (due(now, nextDisplay)) { nextDisplay = now + 3000; updateDisplay(); }
  if (due(now, nextReport)) { nextReport = now + 5000; report(); }
  if (!configured) { safeOutputs(); delay(10); return; }
  if (feeding && due(now, feedDeadline)) { safeOutputs(); persistTerminal("succeeded"); }
  if (relayOn && due(now, relayDeadline)) safeOutputs();
  if (pumpOn && due(now, pumpDeadline)) safeOutputs();
  bool connected = WiFi.status() == WL_CONNECTED;
  if (!connected) {
    if (connectedBefore) {
      bool interrupted = feeding; safeOutputs(); if (interrupted) persistTerminal("failed");
      offlineAt = now; connectedBefore = false;
    }
    if (due(now, nextWifi)) {
      WiFi.disconnect(); WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      nextWifi = now + retryInterval(failures);
    }
    if (now - offlineAt > 300000UL) { safeOutputs(); ESP.restart(); }
    delay(1); return;
  }
  if (!connectedBefore) {
    safeOutputs(); connectedBefore = true; failures = 0;
    Serial.printf("WiFi tersambung, IP %s\n", WiFi.localIP().toString().c_str());
    configTime(0, 0, NTP_SERVER); nextNetwork = now;
  }
  // No fabricated epoch timestamps and no commands before NTP synchronization.
  if (time(nullptr) < 1704067200 || feeding || !due(now, nextNetwork)) { delay(1); return; }
  String response; int status;
  String devicePath = "/api/device/devices/" + String(DEVICE_ID) + "/commands";
  if (currentId.length() && terminalStatus.length()) {
    JsonDocument body; body["status"] = terminalStatus; String payload; serializeJson(body, payload);
    status = requestApi(devicePath + "/" + currentId + "/ack", payload, response);
    // 409 is terminal/expired according to this server contract; never actuate again.
    if (status == 200 || status == 409) {
      if (!journal.remove("pending")) { configured = false; safeOutputs(); return; }
      currentId = ""; terminalStatus = "";
    }
  } else if (pendingTelemetry.length() || due(now, nextTelemetry)) {
    if (!pendingTelemetry.length()) buildTelemetry();
    status = requestApi("/api/devices/" + String(DEVICE_ID) + "/telemetry", pendingTelemetry, response);
    lastTelemetryStatus = status;
    if (status == 201 || status == 409 || status == 422) { pendingTelemetry = ""; nextTelemetry = millis() + 10000; }
  } else if (actuatorsEnabled()) {
    status = requestApi(devicePath, "", response);
    if (status == 200) {
      JsonDocument body;
      if (!deserializeJson(body, response) && body["commands"].is<JsonArray>()) {
        for (JsonObject command : body["commands"].as<JsonArray>()) {
          acceptCommand(command); if (currentId.length()) break;
        }
      } else status = -3;
    }
  } else {
    // Without an enabled actuator there is nothing to poll for; wait for the next telemetry slot.
    delay(1); return;
  }
  if (status >= 200 && status < 300) { failures = 0; nextNetwork = millis() + 2000; }
  else { nextNetwork = millis() + retryInterval(failures); }
  delay(1);
}