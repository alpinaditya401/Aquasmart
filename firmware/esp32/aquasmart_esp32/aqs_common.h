#pragma once

#include <Arduino.h>
#include <esp_random.h>

#include "config.local.h"

static_assert(MAX_FEED_SECONDS >= 1 && MAX_FEED_SECONDS <= 30, "Unsafe feeder duration");
static_assert(RELAY_MAX_ON_SECONDS >= 1 && RELAY_MAX_ON_SECONDS <= 30, "Unsafe relay lease");
static_assert(PUMP_MAX_ON_SECONDS >= 1 && PUMP_MAX_ON_SECONDS <= 30, "Unsafe pump lease");
static_assert(SERVO_CLOSED_DEGREES >= 0 && SERVO_CLOSED_DEGREES <= 180, "Invalid closed angle");
static_assert(SERVO_OPEN_DEGREES >= 0 && SERVO_OPEN_DEGREES <= 180, "Invalid open angle");
static_assert(TANK_HEIGHT_CM >= 1 && TANK_HEIGHT_CM <= 500, "The server accepts a tank height of 1-500 cm");
// GPIO34-39 have no output driver, so a pump on those pins could never switch anything.
static_assert(PIN_PUMP >= 0 && PIN_PUMP <= 33, "Pump needs an output-capable GPIO");
static_assert(PIN_PUMP != PIN_RELAY && PIN_PUMP != PIN_SERVO && PIN_PUMP != PIN_TEMPERATURE
              && PIN_PUMP != PIN_ULTRASONIC_TRIG && PIN_PUMP != PIN_ULTRASONIC_ECHO
              && PIN_PUMP != PIN_LCD_SDA && PIN_PUMP != PIN_LCD_SCL, "Pump pin must not be shared");

enum AnalogChannel { CH_TURBIDITY, CH_SOIL_PH, CH_TDS, CH_COUNT };

// State the module headers share; each group is defined next to the code that owns it.
extern String currentId, terminalStatus, pendingTelemetry, sessionId;
extern bool configured, storageReady, connectedBefore, feeding, relayOn, pumpOn, adcReady;
extern uint32_t feedDeadline, relayDeadline, pumpDeadline, nextNetwork, nextTelemetry, nextWifi, offlineAt;
extern uint32_t failures;
extern float temperature;
extern int filteredRaw[CH_COUNT], filteredMv[CH_COUNT];
extern int lastTelemetryStatus;

inline bool due(uint32_t now, uint32_t deadline) { return int32_t(now - deadline) >= 0; }

// The caller keeps the counter so the network schedule owns the failure count.
inline uint32_t retryInterval(uint32_t &failureCount) {
  unsigned exponent = failureCount < 6 ? failureCount++ : 6;
  uint32_t interval = 1000UL << exponent;
  return (interval > 60000 ? 60000 : interval) + esp_random() % 1000;
}