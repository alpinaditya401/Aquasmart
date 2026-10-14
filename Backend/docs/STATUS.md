# STATUS.md — Status item pengerjaan (per 2026-10-11)

> **Dokumen ini menunggu approval pengajar.** Tidak ada klaim "disetujui".

Legenda: `done` = acceptance criteria terpenuhi + ada bukti.
`blocked-human` = butuh tindakan manusia. `out-of-scope` = tidak dikerjakan
iterasi ini. Tidak ada `done` tanpa bukti.

## Item 1 — Keamanan (repo)

| Sub-item | Status | Bukti |
|---|---|---|
| 1a .gitignore secrets | done | commit `4223d37` |
| 1b git ls-files bersih | done | output: "BERSIH: tidak ada file sensitif ter-track" |
| 1c .env.example placeholder | done | commit `4223d37` (tanpa nilai asli) |
| 1d docs/HUMAN_ACTIONS.md | done | commit `4223d37` |
| Hapus file dari Drive + rotasi kredensial | blocked-human | `docs/HUMAN_ACTIONS.md` §1–§2 |

## Item 2 — Backend P1

| Sub-item | Status | Bukti |
|---|---|---|
| PATCH /api/profile | done | `tests/test_p1.py` (3 test) — commit `f7eb566` |
| POST /api/devices/claim | done | `tests/test_p1.py` (3 test) |
| PATCH /api/devices/{id} | done | `tests/test_p1.py` (3 test: ok/403/404) |
| POST /api/devices/{id}/key/rotate | done | `tests/test_p1.py` (2 test: key sekali tampil, lama invalid) |
| POST /api/alerts/{id}/acknowledge | done | `tests/test_p1.py` (2 test: 409 ack ulang) |
| Schedules CRUD | done | `tests/test_p1.py` (4 test) — deviasi `time`+`duration` lihat BLOCKERS.md §4 |
| PUT /api/settings/thresholds + rule versions | done | `tests/test_p1.py` (4 test) |
| Total | done | **47/47 test hijau** |

## Item 3 — Backend P2

| Sub-item | Status | Bukti |
|---|---|---|
| POST heartbeat → 204 | done | `tests/test_p2.py` (2 test) — commit `acbb9a7` |
| GET telemetry/raw cursor | done | `tests/test_p2.py` (2 test) |
| Feeding logs create+list | done | `tests/test_p2.py` (1 test) |
| Rule versions (version+1) | done | `tests/test_p2.py` (1 test) |
| Observations create+list | done | `tests/test_p2.py` (3 test) |
| Export CSV streaming | done | `tests/test_p2.py` (2 test) |
| Field `source` + backfill simulated | done | `tests/test_p2.py` (3 test); migrasi `app/migrate.py` |
| Total | done | **61/61 test hijau** |

## Item 4 — Scheduler & rate limit

| Sub-item | Status | Bukti |
|---|---|---|
| `flask expire-commands` CLI | done | `tests/test_sched.py` (2 test) — commit `bb0125e` |
| Job terjadwal SCHEDULER_ENABLED | done | `tests/test_sched.py` (1 test) |
| Rate limit Redis / in-memory | done | `tests/test_sched.py` (2 test, kedua jalur) |
| Total | done | **66/66 test hijau** |

## Item 5 — Out of scope

| Sub-item | Status | Bukti |
|---|---|---|
| docs/SCOPE.md | done | commit `68bbd60` |

## Item 6 — Frontend & deploy

| Sub-item | Status | Bukti |
|---|---|---|
| Grep hardcode URL PHP | done | tidak ada (hanya komentar) — commit `1658ee5` |
| CORS via CORS_ORIGINS | done | `tests/test_sched.py` (1 test preflight) |
| GET /healthz | done | `tests/test_sched.py` (1 test) |
| Procfile gunicorn | done | terverifikasi isinya |
| docs/DEPLOY.md | done | eksplisit "belum dieksekusi" |
| docs/E2E_CHECKLIST.md | done | semua "belum dites" |
| Deploy aktual Railway/Vercel | blocked-human | butuh SECRET_KEY, pilihan DB, upload SQLite |

## Item 7 — Hardware

| Sub-item | Status | Bukti |
|---|---|---|
| hardware/FLASH_TEST_PLAN.md | done | commit `993a2f8`; status: dites 2026-10-10 semua berhasil |
| TURBIDITY_CALIBRATED=false | done | `config.example.h` (belum verifikasi compile → BLOCKERS.md §1) |
| PH_STATUS=DEFERRED_NEXT_YEAR | done | `config.example.h` |
| TDS "belum dikalibrasi" | done | komentar `config.example.h` + README firmware |
| docs/CONTRACT_PUMP_AERATOR.md | done | commit `993a2f8` |
| Stub setPump/setAerator | done | `aqs_actuators.h` (belum verifikasi compile) |
| Flash/wiring fisik | blocked-human | agent tidak bisa flash atau wiring |

## Item 8 — ML & Flutter

| Sub-item | Status | Bukti |
|---|---|---|
| ml/inference_adapter.py | done | `predict()` → None terverifikasi via CLI |
| Flutter | out-of-scope | backlog di `docs/SCOPE.md` |

## Item 9 — Dokumen SKPL

| Sub-item | Status | Bukti |
|---|---|---|
| 7 diagram Mermaid | done | `docs/uml/*.mmd` — validasi mmdc gagal → BLOCKERS.md §2 |
| "menunggu approval pengajar" | done | README.md + STATUS.md |
| docs/NFR_MEASUREMENT.md | done | metode saja, tanpa hasil — commit `06b2824` |

## Ringkasan akhir

- **Test hijau: 68/68** (`pytest tests/ -q`), tidak pernah turun dari 27.
- **Commit: 10** (semua format feat/docs, tanpa force-push).
- **Blocked-human**: hapus file sensitif Drive + rotasi (HUMAN_ACTIONS.md),
  deploy production, flash/wiring fisik.
- **Deviasi terdokumentasi**: BLOCKERS.md §4 (schedules), §5 (TDS threshold).
