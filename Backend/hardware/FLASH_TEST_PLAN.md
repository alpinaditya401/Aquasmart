# FLASH_TEST_PLAN.md — Prosedur flash & uji hardware ESP32

> **Status: SUDAH DITES pada 2026-10-10 — semua berhasil** (ESP32, sensor
> turbidity/TDS/suhu/level, aktuator). Dokumen ini adalah prosedur
> referensi untuk pengulangan/pemeliharaan, bukan rencana yang belum jalan.

## 1. Toolchain

- Arduino IDE 2 atau arduino-cli 1.5.1
- Board: **DOIT ESP32 DEVKIT V1** (fallback: ESP32 Dev Module)
- Core: esp32 by Espressif Systems **3.0.7**
- Board-manager URL: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
- Library: ArduinoJson 7.4.3, OneWire 2.3.8, DallasTemperature 4.0.6,
  ESP32Servo 3.2.1/3.0.5, LiquidCrystal I2C 1.1.2

## 2. Langkah flash

1. Salin `firmware/esp32/config.example.h` → `aquasmart_esp32/config.local.h`
   (jangan distribusikan salinan privat ini).
2. Isi `WIFI_SSID`, `WIFI_PASSWORD`, `DEVICE_ID`, `DEVICE_KEY`, `API_BASE`,
   `ROOT_CA` (ganti semua `GANTI_SEBELUM_UPLOAD`).
3. Nyalakan flag `_WIRING_CONFIRMED` per komponen yang sudah dicek wiring-nya.
4. Verify (compile) dulu — simpan log compile + versi library.
5. Pilih port COM aktual → Upload. Pastikan kabel **data** Micro-USB
   (bukan kabel power-only) dan driver USB-serial terinstal.
6. Buka Serial Monitor 115200 — pastikan muncul
   "Konfigurasi termuat, keluaran aman."

## 3. Tabel wiring pin

| Fungsi | Pin ESP32 | Catatan |
|---|---|---|
| DS18B20 (suhu) | GPIO4 | OneWire, konversi async 12-bit |
| Turbidity (analog) | GPIO34 | ADC1; output **raw**, bukan NTU |
| Soil pH (analog) | GPIO32 | Placeholder tanah, **bukan pH air** |
| TDS (analog) | GPIO35 | ADC1; **belum dikalibrasi** |
| Ultrasonik TRIG | GPIO27 | HC-SR04 |
| Ultrasonik ECHO | GPIO25 | **Wajib voltage divider** (ECHO 5V → 3,3V) |
| LCD SDA / SCL | GPIO21 / GPIO22 | I2C 0x27 |
| Servo feeder | GPIO18 | Kalibrasi sudut mekanis dulu |
| Relay aerator | GPIO23 | Trigger 3,3V terkonfirmasi; lease 30 dtk |
| Pompa (driver trigger) | GPIO14 | Trigger 3,3V, **bukan** kabel daya pompa |

Aturan: sensor analog wajib GPIO32–39 (ADC1; ADC2 mati saat WiFi aktif).
`static_assert` menolak pin ganda dan pin tanpa output driver.

## 4. Kriteria lulus per sensor (hasil 2026-10-10: semua lulus)

| Sensor | Kriteria lulus |
|---|---|
| DS18B20 | Serial menampilkan suhu masuk akal (°C); `temperature_status=ok` di payload |
| Turbidity | `turbidity_adc`/`turbidity_mv` berubah saat air keruh/jernih; **tanpa klaim NTU** (`TURBIDITY_CALIBRATED=false`) |
| TDS | `tds_adc`/`tds_mv` terbaca; estimasi ppm tampil dengan label **estimasi/belum dikalibrasi** |
| Ultrasonik | `water_distance_cm` stabil ±1 cm; level % konsisten dengan tinggi air aktual |
| Feeder servo | Bergerak buka→tutup sesuai durasi command; kembali tutup sebelum ACK |
| Relay aerator | Klik ON/OFF terdengar; OFF otomatis setelah lease 30 detik |
| Pompa | Driver terpicu via GPIO14; **terpisah** dari jalur aerator |

## 5. Catatan kontrak data

- `ph_sensor` selalu `soil_placeholder`, `calibrated` selalu `false`.
- `PH_STATUS = "DEFERRED_NEXT_YEAR"` — sensor pH air ditunda ke tahun depan.
- ACK `succeeded` = pin diperintahkan, **bukan** bukti motor bergerak.
