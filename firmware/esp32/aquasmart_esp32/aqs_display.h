#pragma once

// LCD and Serial output. These keep running without WiFi so wiring can be checked on the bench.
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <math.h>
#include "aqs_common.h"
#include "aqs_network.h"
#include "aqs_sensors.h"

LiquidCrystal_I2C lcd(LCD_I2C_ADDRESS, 16, 2);
bool showSensorPage = true;

String sensorLine(bool tdsRow) {
  if (tdsRow) {
    if (!TDS_WIRING_CONFIRMED) return "TDS nonaktif";
    if (!tdsReady()) return "TDS membaca...";
    return "TDS " + String(lround(tdsPpmEstimate(filteredMv[CH_TDS]))) + " ppm";
  }
  if (!ULTRASONIC_WIRING_CONFIRMED) return "Air nonaktif";
  float distance = waterDistanceCm();
  if (!isfinite(distance)) return "Air tak terbaca";
  return "Air " + String(lround(waterLevelPercent(distance))) + "% " + String(distance, 1) + "cm";
}

String networkLine() {
  if (!configured) return "Konfig belum isi";
  if (WiFi.status() != WL_CONNECTED) return "WiFi mencari...";
  if (time(nullptr) < 1704067200) return "Tunggu jam NTP";
  switch (lastTelemetryStatus) {
    case 0: return "Belum kirim";
    case 201: return "Terkirim ke web";
    case 401: return "Kunci salah 401";
    case 422: return "Data ditolak 422";
    default: return lastTelemetryStatus < 0 ? "Server tak jawab" : "HTTP " + String(lastTelemetryStatus);
  }
}

void printLine(int row, String text) {
  while (text.length() < 16) text += ' ';
  lcd.setCursor(0, row); lcd.print(text.substring(0, 16));
}

void updateDisplay() {
  if (!ENABLE_LCD) return;
  if (showSensorPage) {
    printLine(0, sensorLine(true));
    printLine(1, sensorLine(false));
  } else {
    printLine(0, WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString() : "WiFi putus");
    printLine(1, networkLine());
  }
  showSensorPage = !showSensorPage;
}

void report() {
  String tds = tdsReady() ? sensorLine(true) + " (" + String(filteredMv[CH_TDS]) + " mV, estimasi)" : sensorLine(true);
  String temp = !DS18B20_WIRING_CONFIRMED ? "Suhu nonaktif"
    : isfinite(temperature) ? "Suhu " + String(temperature, 1) + " C" : "Suhu tak terbaca";
  Serial.printf("%s | %s | %s | %s\n", tds.c_str(), sensorLine(false).c_str(), temp.c_str(), networkLine().c_str());
}