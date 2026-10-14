#pragma once

// Actuators. A terminal ACK means the output pin was ordered, not that the motor turned.
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include <Preferences.h>
#include <ctype.h>
#include <time.h>
#include "aqs_common.h"

Servo feeder;
Preferences journal;
bool feeding = false, relayOn = false, pumpOn = false;
uint32_t feedDeadline = 0, relayDeadline = 0, pumpDeadline = 0;
String currentId, terminalStatus;

bool relayEnabled() { return ENABLE_RELAY && RELAY_3V3_COMPATIBLE_CONFIRMED; }
bool pumpEnabled() { return ENABLE_PUMP && PUMP_DRIVER_WIRING_CONFIRMED; }
bool actuatorsEnabled() { return ENABLE_FEEDER || relayEnabled() || pumpEnabled(); }

void safeOutputs() {
  if (ENABLE_FEEDER && feeder.attached()) feeder.write(SERVO_CLOSED_DEGREES);
  if (relayEnabled()) digitalWrite(PIN_RELAY, RELAY_ACTIVE_LOW ? HIGH : LOW);
  if (pumpEnabled()) digitalWrite(PIN_PUMP, PUMP_ACTIVE_LOW ? HIGH : LOW);
  feeding = false;
  relayOn = false;
  pumpOn = false;
}

// --- Kontrak pompa vs aerator (SKPL V4.0) ---
// Pompa dan aerator adalah aktuator TERPISAH; pompa BUKAN alias aerator.
// Interface stub untuk dokumentasi kontrak — logika aktual (dengan lease
// lokal 30 detik dan safety check) tetap di acceptCommand().
//   setAerator(true)  → menggerakkan relay aerator (PIN_RELAY)
//   setPump(true)     → menggerakkan driver pompa (PIN_PUMP, trigger 3.3V,
//                       BUKAN kabel daya pompa langsung)
inline void setAerator(bool on) {
  // Stub kontrak: implementasi penuh ada di cabang "aerator" acceptCommand().
  (void)on;
}
inline void setPump(bool on) {
  // Stub kontrak: implementasi penuh ada di cabang "pump" acceptCommand().
  (void)on;
}

// One NVS value is the recovery record. A reset during actuation recovers as failed.
bool persistTerminal(const String &status) {
  if (!storageReady || journal.putString("pending", currentId + "|" + status) == 0) {
    safeOutputs(); configured = false; return false;
  }
  terminalStatus = status;
  return true;
}

bool validId(const String &id) {
  if (id.length() != 32) return false;
  for (unsigned i = 0; i < id.length(); ++i) if (!isxdigit(id[i]) || isupper(id[i])) return false;
  return true;
}

void acceptCommand(JsonObject command) {
  String id = command["id"] | "";
  if (!validId(id) || String(command["device_id"] | "") != DEVICE_ID) return;
  if (!command["simulation"].is<bool>() || command["simulation"].as<bool>()) return;
  if (!command["expires_at"].is<long>() || !command["duration"].is<int>() || !command["value"].is<bool>()) return;
  // The server never reopens terminal IDs. Retain a bounded journal as extra replay protection.
  for (int i = 0; i < 8; ++i) {
    String slot = "seen" + String(i);
    if (journal.getString(slot.c_str(), "") == id) return;
  }
  currentId = id;
  if (!persistTerminal("failed")) return;
  unsigned slot = journal.getUInt("slot", 0) % 8;
  String key = "seen" + String(slot);
  if (!journal.putString(key.c_str(), id) || !journal.putUInt("slot", (slot + 1) % 8)) {
    safeOutputs(); configured = false; return;
  }
  long expires = command["expires_at"].as<long>();
  int duration = command["duration"].as<int>(); bool value = command["value"].as<bool>();
  String actuator = command["actuator"] | "";
  if (expires <= time(nullptr)) { persistTerminal("timeout"); return; }
  if (actuator == "feeder" && ENABLE_FEEDER && duration >= 1 && duration <= int(MAX_FEED_SECONDS)) {
    if (!value) { safeOutputs(); persistTerminal("succeeded"); return; }
    if (expires - time(nullptr) < duration + 2) { persistTerminal("timeout"); return; }
    feeder.write(SERVO_OPEN_DEGREES); feeding = true;
    feedDeadline = millis() + duration * 1000UL; terminalStatus = "";
  } else if (actuator == "aerator" && relayEnabled() && duration == 0) {
    digitalWrite(PIN_RELAY, value == RELAY_ACTIVE_LOW ? LOW : HIGH);
    relayOn = value; relayDeadline = millis() + RELAY_MAX_ON_SECONDS * 1000UL;
    persistTerminal("succeeded");
  } else if (actuator == "pump" && pumpEnabled() && duration == 0) {
    digitalWrite(PIN_PUMP, value == PUMP_ACTIVE_LOW ? LOW : HIGH);
    pumpOn = value; pumpDeadline = millis() + PUMP_MAX_ON_SECONDS * 1000UL;
    persistTerminal("succeeded");
  }
  // Disabled/unsupported commands retain the prewritten failed result.
}