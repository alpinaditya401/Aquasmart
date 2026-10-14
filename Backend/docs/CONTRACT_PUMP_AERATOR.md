# CONTRACT_PUMP_AERATOR.md — Kontrak pompa vs aerator (SKPL V4.0)

## Aturan keras

1. **Pompa dan aerator adalah aktuator terpisah.** Pompa BUKAN alias aerator,
   dan sebaliknya. Dilarang menyamarkan satu sebagai yang lain di API,
   firmware, maupun UI.
2. Perintah `aerator` → relay aerator (GPIO23, trigger 3,3V).
   Perintah `pump` → driver pompa (GPIO14, trigger 3,3V — **bukan** kabel
   daya pompa langsung).
3. Masing-masing dibatasi lease lokal 30 detik lalu OFF otomatis.
4. ACK `succeeded` berarti GPIO diperintahkan, **bukan** bukti fisik
   (motor/pompa benar-benar bergerak).

## Status implementasi

| Lapisan | Status |
|---|---|
| Firmware | ✅ Terpisah: cabang `aerator` (relay) dan `pump` (GPIO14) di `acceptCommand()`; stub interface `setAerator(bool)` / `setPump(bool)` di `aqs_actuators.h` sebagai dokumentasi kontrak |
| Backend Flask | ⚠️ Parsial: `POST /api/devices/<id>/control` menerima `aerator`/`feeder`/`auto`; nilai `pump` **ditolak** (422) sampai kontrak driver pompa terverifikasi di hardware |
| Frontend | Ikut backend: kontrol pump disembunyikan sampai backend mendukung |

## Yang harus diverifikasi manusia sebelum pump dibuka

- [ ] Driver pompa terkonfirmasi cocok dengan trigger 3,3V GPIO14
- [ ] Tegangan/daya suplai pompa sesuai spesifikasi unit (bukan 12V langsung ke pompa 3V)
- [ ] Uji fisik: command `pump` → pompa menyala → OFF otomatis ≤30 detik
