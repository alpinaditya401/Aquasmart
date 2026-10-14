# Prioritas FR & Timeline — AquaSmart Flask Backend

Acuan: SRS AquaSmart v1 (FR-001..FR-034, selaras PRD). Status per 10 Okt 2026 ~21:30 WIB.

## Status implementasi saat ini

| Status | FR |
|---|---|
| ✅ Selesai (27/27 test hijau) | FR-001 register, FR-002 login, FR-003 logout, FR-004 me, FR-006 health, FR-007 rules, FR-008 devices, FR-013 telemetry ingest, FR-015 readings, FR-016 poll commands, FR-017 ack, FR-021 reports, FR-022 alerts, FR-025 thresholds (GET), FR-018 control (enqueue + idempotensi + auto-mode + tolak simulasi) |
| ⬜ Belum | sisanya (lihat timeline) |

**Seluruh 12 FR Must sudah selesai.** Koneksi frontend↔backend terbukti live
(BFF Next.js hanya perlu `AQUASMART_API_URL` menunjuk ke Flask — tanpa ubah kode).

## Prioritas & timeline per FR

### P0 — Must (SELESAI ✅)
| FR | Endpoint | Status |
|---|---|---|
| FR-001 | POST /api/auth/register | ✅ |
| FR-002 | POST /api/auth/login | ✅ |
| FR-003 | POST /api/auth/logout | ✅ |
| FR-004 | GET /api/auth/me | ✅ |
| FR-006 | GET /api/health | ✅ |
| FR-007 | GET /api/rules | ✅ |
| FR-008 | GET /api/devices | ✅ |
| FR-013 | POST /api/devices/{id}/telemetry | ✅ |
| FR-015 | GET /api/devices/{id}/readings | ✅ |
| FR-016 | GET /api/device/devices/{id}/commands | ✅ |
| FR-017 | POST /api/device/devices/{id}/commands/{cid}/ack | ✅ |
| FR-021 | GET /api/reports | ✅ |

### P1 — Should (target: 11–12 Okt 2026)
| FR | Endpoint | Estimasi | Catatan |
|---|---|---|---|
| FR-022 | GET /api/alerts | ✅ selesai | — |
| FR-023 | POST /api/alerts/{id}/acknowledge | 0,5 hari | + audit log |
| FR-005 | PATCH /api/profile | 0,5 hari | validasi nama/phone |
| FR-009 | POST /api/devices/claim | 0,5 hari | serial + kode aktivasi |
| FR-010 | PATCH /api/devices/{id} | 0,5 hari | nama/lokasi |
| FR-011 | POST /api/devices/{id}/key/rotate | 0,5 hari | kunci baru 1x tampil |
| FR-018 | POST /api/devices/{id}/control | ✅ selesai 11 Okt (12 test baru) | enqueue + idempotensi request_id + 409 aktuator sibuk + auto=mode (tanpa antrian) + tolak simulation + admin-only + 403 csrf_mismatch |
| FR-024 | CRUD /api/devices/{id}/schedules | 1,5 hari | validasi HH:MM, zona waktu eksplisit |
| FR-025 | PUT /api/settings/thresholds | 0,5 hari | admin + snapshot rule_versions |

### P2 — Could (target: 13–14 Okt 2026)
| FR | Estimasi |
|---|---|
| FR-012 heartbeat, FR-014 raw telemetry | 0,5 hari |
| FR-019 riwayat commands, FR-020 feeding logs | 0,5 hari |
| FR-026 rule versions | 0,5 hari |
| FR-027 observations CRUD | 1 hari |
| FR-028 export CSV | 1 hari |

### Won't — v1.1
FR-029 s.d. FR-034 (workspace, product/units, audit-logs — path audit belum terverifikasi).

## Total sisa estimasi
- P1: ±4 hari kerja → selesai 12 Okt bila dikerjakan berurutan, bisa paralel per domain.
- P2: ±3 hari.
