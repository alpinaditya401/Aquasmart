#pragma once

// WiFi, TLS and the server contract. No command is accepted before NTP synchronisation.
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <math.h>
#include <time.h>
#include "aqs_actuators.h"
#include "aqs_sensors.h"

String sessionId, pendingTelemetry;
bool configured = false, storageReady = false, connectedBefore = false;
uint32_t nextNetwork = 0, nextTelemetry = 0, nextWifi = 0, offlineAt = 0;
uint32_t failures = 0;
int lastTelemetryStatus = 0;

bool privateHttp() {
  String base(API_BASE);
  if (!ALLOW_PRIVATE_LAN_HTTP || !base.startsWith("http://")) return false;
  String host = base.substring(7); int colon = host.indexOf(':');
  if (colon >= 0) host = host.substring(0, colon);
  IPAddress ip;
  if (!ip.fromString(host)) return false;
  return ip[0] == 10 || (ip[0] == 172 && ip[1] >= 16 && ip[1] <= 31) || (ip[0] == 192 && ip[1] == 168);
}

int requestApi(const String &path, const String &payload, String &response) {
  WiFiClient plain;
  WiFiClientSecure secure;
  HTTPClient http;
  String base(API_BASE);
  if (base.startsWith("https://")) {
    if (DEVELOPMENT_INSECURE_TLS) secure.setInsecure();
    else secure.setCACert(ROOT_CA);
    secure.setHandshakeTimeout(3);
    if (!http.begin(secure, base + path)) return -1;
  } else {
    if (!privateHttp() || !http.begin(plain, base + path)) return -1;
  }
  http.setConnectTimeout(2000); http.setTimeout(2000);
  http.setFollowRedirects(HTTPC_DISABLE_FOLLOW_REDIRECTS);
  http.useHTTP10(true);
  http.addHeader("X-Device-Key", DEVICE_KEY);
  http.addHeader("Content-Type", "application/json");
  int status = payload.length() ? http.POST(payload) : http.GET();
  response = "";
  if (status > 0) {
    auto stream = http.getStreamPtr(); uint32_t began = millis();
    while ((http.connected() || stream->available()) && millis() - began < 2000) {
      while (stream->available()) {
        if (response.length() >= 8192) { http.end(); return -2; }
        response += char(stream->read());
      }
      delay(1);
    }
  }
  http.end(); return status;
}

void buildTelemetry() {
  JsonDocument body;
  time_t utc = time(nullptr); char timestamp[24]; struct tm tmUtc;
  gmtime_r(&utc, &tmUtc); strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%SZ", &tmUtc);
  body["device_id"] = DEVICE_ID; body["created_at"] = timestamp;
  body["provenance"] = "device"; body["simulation"] = false; body["source_session"] = sessionId;
  body["temperature"] = nullptr;
  body["temperature_status"] = DS18B20_WIRING_CONFIRMED ? "disconnected" : "unverified";
  if (isfinite(temperature)) { body["temperature"] = temperature; body["temperature_status"] = "ok"; }
  for (int i = 0; i < CH_COUNT; ++i) {
    body[String(analogPrefix[i]) + "_adc"] = nullptr; body[String(analogPrefix[i]) + "_mv"] = nullptr;
    if (analogEnabled[i] && adcReady && filteredMv[i] <= 3300) {
      body[String(analogPrefix[i]) + "_adc"] = filteredRaw[i];
      body[String(analogPrefix[i]) + "_mv"] = filteredMv[i];
    }
  }
  body["turbidity_sensor_mv"] = nullptr; body["turbidity_mapping_percent"] = nullptr;
  if (!body["turbidity_mv"].isNull()) {
    float sensorMv = filteredMv[CH_TURBIDITY] / 0.6f;
    body["turbidity_sensor_mv"] = sensorMv;
    body["turbidity_mapping_percent"] = constrain(100.0f * (1.0f - sensorMv / 5000.0f), 0.0f, 100.0f);
  }
  body["water_distance_cm"] = nullptr; body["tank_height_cm"] = nullptr;
  float distance = waterDistanceCm();
  if (ULTRASONIC_WIRING_CONFIRMED && isfinite(distance)) {
    body["water_distance_cm"] = round(double(distance) * 10.0) / 10.0;
    body["tank_height_cm"] = double(TANK_HEIGHT_CM);
  }
  body["ph_sensor"] = "soil_placeholder"; body["calibrated"] = false;
  pendingTelemetry = ""; serializeJson(body, pendingTelemetry);
}