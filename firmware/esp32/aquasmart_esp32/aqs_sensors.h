#pragma once

// Sensor sampling. Every value here is raw and uncalibrated; the server derives ppm and level.
#include <OneWire.h>
#include <DallasTemperature.h>
#include <math.h>
#include "aqs_common.h"

// ADC2 stops working once WiFi starts, so every analog sensor has to sit on ADC1.
constexpr bool onAdc1(int pin) { return pin >= 32 && pin <= 39; }
static_assert(onAdc1(PIN_TURBIDITY) && onAdc1(PIN_SOIL_PH) && onAdc1(PIN_TDS), "Analog sensors need GPIO32-39");
static_assert(PIN_TDS != PIN_TURBIDITY && PIN_TDS != PIN_SOIL_PH && PIN_TURBIDITY != PIN_SOIL_PH,
              "Analog sensors must not share a pin");

const int analogPins[CH_COUNT] = {PIN_TURBIDITY, PIN_SOIL_PH, PIN_TDS};
const bool analogEnabled[CH_COUNT] = {TURBIDITY_VOLTAGE_CONFIRMED, SOIL_PH_VOLTAGE_CONFIRMED, TDS_WIRING_CONFIRMED};
const char *const analogPrefix[CH_COUNT] = {"turbidity", "soil_ph", "tds"};

OneWire oneWire(PIN_TEMPERATURE);
DallasTemperature thermometer(&oneWire);
int adcIndex = 0, raw[CH_COUNT][9] = {}, millivolts[CH_COUNT][9] = {};
int filteredRaw[CH_COUNT] = {}, filteredMv[CH_COUNT] = {};
bool adcReady = false;
bool waitingTemperature = false;
uint32_t conversionAt = 0;
float temperature = NAN;
float echoes[5] = {NAN, NAN, NAN, NAN, NAN};
int echoIndex = 0;
uint32_t nextAdc = 0, nextEcho = 0;

int median(int *values) {
  int sorted[9]; memcpy(sorted, values, sizeof(sorted));
  for (int i = 1; i < 9; ++i) {
    int value = sorted[i], j = i;
    while (j > 0 && sorted[j - 1] > value) { sorted[j] = sorted[j - 1]; --j; }
    sorted[j] = value;
  }
  return sorted[4];
}

float readEchoCm() {
  digitalWrite(PIN_ULTRASONIC_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(PIN_ULTRASONIC_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(PIN_ULTRASONIC_TRIG, LOW);
  // A 30 ms timeout covers about 5 m and bounds how long loop() can stall.
  unsigned long echo = pulseIn(PIN_ULTRASONIC_ECHO, HIGH, 30000);
  return echo == 0 ? NAN : echo * 0.0343f / 2.0f;
}

float waterDistanceCm() {
  float valid[5]; int count = 0;
  for (float echo : echoes) if (isfinite(echo)) valid[count++] = echo;
  // Fewer than three echoes out of five counts as no reading rather than a noisy one.
  if (count < 3) return NAN;
  for (int i = 1; i < count; ++i) {
    float value = valid[i]; int j = i;
    while (j > 0 && valid[j - 1] > value) { valid[j] = valid[j - 1]; --j; }
    valid[j] = value;
  }
  float distance = valid[count / 2];
  return distance <= 500 ? distance : NAN;
}

// Display only; the server derives the stored level and ppm from the raw values with the same formulas.
float waterLevelPercent(float distance) {
  return constrain((TANK_HEIGHT_CM - distance) / TANK_HEIGHT_CM * 100.0f, 0.0f, 100.0f);
}

float tdsPpmEstimate(int mv) {
  float volts = mv / 1000.0f;
  return (133.42f * volts * volts * volts - 255.86f * volts * volts + 857.39f * volts) * 0.5f;
}

bool tdsReady() { return TDS_WIRING_CONFIRMED && adcReady && filteredMv[CH_TDS] <= 3300; }

void sampleSensors(uint32_t now) {
  if (due(now, nextAdc)) {
    nextAdc = now + 20;
    for (int i = 0; i < CH_COUNT; ++i) if (analogEnabled[i]) {
      raw[i][adcIndex] = analogRead(analogPins[i]);
      millivolts[i][adcIndex] = analogReadMilliVolts(analogPins[i]);
    }
    if (++adcIndex == 9) {
      adcIndex = 0; adcReady = true;
      for (int i = 0; i < CH_COUNT; ++i) { filteredRaw[i] = median(raw[i]); filteredMv[i] = median(millivolts[i]); }
    }
  }
  if (ULTRASONIC_WIRING_CONFIRMED && due(now, nextEcho)) {
    nextEcho = now + 200;
    echoes[echoIndex] = readEchoCm();
    echoIndex = (echoIndex + 1) % 5;
  }
  if (DS18B20_WIRING_CONFIRMED) {
    if (!waitingTemperature) {
      thermometer.requestTemperatures(); conversionAt = now; waitingTemperature = true;
    } else if (now - conversionAt >= 800) {
      float value = thermometer.getTempCByIndex(0);
      temperature = value >= -55 && value <= 125 ? value : NAN;
      waitingTemperature = false;
    }
  }
}