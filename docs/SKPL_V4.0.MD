# Spesifikasi Kebutuhan Perangkat Lunak AquaSmart AIoT

Versi: **V4.0**. Tanggal: 11 Oktober 2026. Status: baseline kebutuhan kerja untuk proyek Block; persetujuan pengajar dan penutupan setiap kebutuhan belum dicatat. Dokumen ini **menggantikan SKPL V3.0** (5 Oktober 2026).

## 0. Riwayat perubahan

| Versi | Tanggal | Perubahan |
| --- | --- | --- |
| V1.0 | — | Baseline konsolidasi historis (24 FR, 15 NFR). |
| V3.0 | 5 Okt 2026 | 14 kelompok fungsi (V3-FR01–V3-FR14), 15 NFR (V3-NFR01–V3-NFR15), 7 matkul, 3 matkul dikeluarkan. Backend produk: PHP 8. |
| **V4.0** | **11 Okt 2026** | **Backend produk diganti PHP 8 → Flask (Python)** atas keputusan pemilik. Kontrak API dipertahankan identik (firmware & frontend tidak berubah). Flask bukan lagi "praktikum terpisah". Matriks FR/NFR/matkul tidak berubah. |

## 1. Tujuan dan perubahan cakupan

AquaSmart menggabungkan pemantauan air, backend, antarmuka web/mobile, machine learning Python serta perangkat IoT untuk satu kolam. Tahap awal menggunakan simulasi; tahap berikutnya menggunakan wadah air kecil milik pengguna. SKPL menentukan perilaku yang diperlukan dan cara membuktikannya, bukan menyatakan seluruh fitur sudah selesai.

Pengguna menetapkan cakupan pada 5 Oktober 2026, **diperbarui 11 Oktober 2026**:

| Keputusan | Penerapan pada V4.0 |
| --- | --- |
| Web/PWA, praktikum Flask, Flutter, Docker, ML Python dan IoT tetap masuk | Dipertahankan sebagai bagian produk atau deliverable teknis dengan status masing-masing. |
| **Backend produk: Flask menggantikan PHP 8** (keputusan 11 Okt 2026) | Flask (Python) adalah backend produk aktif. Kontrak API, skema SQLite, dan envelope error dipertahankan identik dengan backend PHP lama sehingga firmware ESP32 dan frontend Next.js tidak perlu diubah. |
| IoT dihitung dalam Block proyek | Sensor, ESP32, komunikasi, command/ACK, kalibrasi dan uji perangkat masuk traceability Block. |
| Tujuh matkul digunakan | Manajemen Proyek, Keamanan Siber, Komputasi Awan, Pemrograman BackEnd, Aplikasi Mobile, Python untuk Sistem Cerdas dan IoT, sesuai daftar pengguna. |
| Penulisan Ilmiah dikeluarkan | Naskah ilmiah, format bab, publikasi serta tugas penulisan bukan kebutuhan atau gate penutupan Block ini. Dokumentasi API/model/test tetap diperlukan secara teknis. |
| Pemrograman Multimedia Interaktif dikeluarkan | Game, AR/VR, animasi edukatif, scene/asset 3D serta demo multimedia bukan requirement Block. UI operasional, grafik sensor dan aksesibilitas tetap diperlukan. |
| Kewirausahaan dikeluarkan | Business plan, pemasaran, penjualan, pembayaran, inventaris komersial dan aktivasi pelanggan bukan requirement Block. Auth serta identitas perangkat tetap diperlukan untuk operasi. |
| Jumlah FR dibuat lebih ringkas | Kebutuhan diorganisasi sebagai 14 kelompok fungsi. Kriteria subfitur dipertahankan dan dapat diuji; satu matkul tidak otomatis membuat FR baru. |

Baseline lama menyebut 24 FR dan 15 NFR; RTM historis juga menyebut FR25/FR26 yang tidak ada pada tabel FR SKPL tersebut. V4.0 memakai ID V3-FR01 sampai V3-FR14 dan V3-NFR01 sampai V3-NFR15 (ID dipertahankan dari V3.0 agar traceability tidak putus). ID lama hanya digunakan pada matriks transisi di bagian 10. Tidak ada kewajiban minimal 24 FR pada baseline ini.

## 2. Cakupan produk dan deliverable Block

### 2.1 Dalam cakupan

- Satu kolam, satu perangkat utama, role admin/viewer dan mode simulasi.
- Backend **Flask (Python)** — pengganti PHP 8 per 11 Okt 2026; SQLite dipakai ulang tanpa migrasi data.
- Ingest/persistensi data, monitoring/histori, aturan ambang, peringatan, kontrol/jadwal dan audit.
- Observasi manual dan laporan/ekspor operasional sesuai prioritas; keduanya tidak dianggap naskah ilmiah atau laporan bisnis.
- Sistem Cerdas Python: eksperimen training/evaluasi serta rancangan integrasi inferensi ML.
- Web/PWA operasional serta Flutter sebagai client/deliverable mobile. Fokus platform Flutter masih perlu ditetapkan; SDK yang terpasang bukan bukti client AquaSmart selesai.
- Docker untuk pengemasan runtime; diagram, kontrak API, skema data dan bukti pengujian sebagai artefak teknis.

### 2.2 Di luar cakupan

Kontribusi tiga matkul pada bagian 1, multi-kolam, gateway WhatsApp/email, layanan AI Agent/LLM wajib, ML yang mengendalikan aktuator otomatis, cloud berbayar 24/7 wajib, serta klaim kesehatan ikan/peningkatan panen tanpa uji. File atau fitur lama pada workspace tidak dihapus oleh perubahan SKPL ini.

Halaman publik, demo 3D atau game yang sudah ada tidak menjadi syarat lulus Block V4.0. Mockup login/dashboard/pengaturan tetap artefak desain antarmuka operasional; mockup tidak dihitung sebagai fungsi runtime tersendiri.

### 2.3 Lingkungan dan batas integrasi

| Lingkungan | Stack/status | Batas |
| --- | --- | --- |
| Produk utama | Next.js/BFF, **Flask (Python)**, SQLite menurut implementasi aktif | Backend PHP 8 digantikan Flask pada 11 Okt 2026; kontrak API identik. Status tes pada README bersifat historis. |
| Sistem Cerdas | Python, pandas, NumPy, scikit-learn, joblib; notebook/pipeline/evaluasi offline tersedia | Adapter inferensi produk belum dibuat. |
| Mobile | Flutter SDK dan counter sample teruji pada target web | Client AquaSmart, APK Android dan build Windows belum terbukti selesai. |
| Perangkat | ESP32 dan inventaris pada bagian 4 | Wiring, firmware fisik, kalibrasi dan aktuasi belum diverifikasi. |

SQLite mengikuti runtime prototype. Keputusan CR-001 terhadap baseline MySQL/MariaDB masih menunggu sponsor; perubahan scope Block tidak dianggap persetujuan CR tersebut.

## 3. Aktor dan istilah

| Aktor | Hak/pekerjaan |
| --- | --- |
| Admin | Membaca kolam yang diizinkan, mengubah ambang/jadwal, meminta command dan meninjau audit. |
| Viewer | Membaca resource kolam yang diizinkan; mutasi ditolak server. |
| Teknisi | Menyiapkan serta menguji perangkat melalui akses yang diberikan; bukan role admin otomatis. |
| ESP32/simulator | Telemetry, heartbeat, polling command dan ACK sesuai identitas/channel. |
| Worker | Pemrosesan occurrence jadwal/expiry sesuai policy dan transaksi. |
| Pengelola eksperimen ML | Menyiapkan data/fitur, mengevaluasi model dan memilih artefak; bukan controller fisik. |

Reading adalah pembacaan sensor bertimestamp. Raw telemetry adalah diagnostik sebelum konversi/kalibrasi mendukung nilai air kanonis. TDS mengukur/menaksir zat padat terlarut dan tidak menggantikan pH atau kekeruhan. Provenance menunjukkan sumber data; calibrated menunjukkan status kalibrasi. ACK adalah hasil protokol dan tidak membuktikan gerak fisik. Prediksi ML berbeda dari reading serta evaluasi ambang saat ini.

## 4. Scope hardware dan machine learning

### 4.1 Inventaris dan lingkungan uji

Pengguna menyebut ESP-0016/ESP32, SEN-0175, DS18B20, TDS Meter V1.0, pompa air mini 3V, micro servo SG90, catu daya 1220 12V DC 2A dan relay 1 kanal berlabel 24V H/L. Sensor pH dan driver belum ada. Varian/pinout, bentuk probe, rating lengkap relay, konversi daya serta kebutuhan saklar/proteksi belum diperiksa.

Wadah persegi panjang diperkirakan beralas 5 x 7 cm dengan tinggi air 7 cm. Jika merupakan ukuran dalam dengan sisi tegak, volume geometris sekitar 245 mL; volume efektif dan kecocokan probe/pompa belum diukur. Tinggi air ini catatan pengguna, bukan sensor level otomatis.

Pompa 3V memerlukan suplai sesuai unit; sumber 12V tidak dihubungkan langsung ke pompa. Relay tidak menurunkan tegangan dan label 24V H/L belum cukup untuk menentukan kecocokan suplai/trigger. Komponen SG90 belum membuktikan feeder yang berfungsi. Pompa air tidak dianggap aerator; kontrak pump/driver serta hasil fisik harus diuji sebelum fitur hardware dibuka.

### 4.2 Sistem Cerdas Python

Source Hari 1/Hari 2 memuat Random Forest untuk prediksi status proksi pH/suhu pada interval lima menit berikutnya dari riwayat pH, TDS dan suhu. Eksperimen Isolation Forest untuk anomali sensor tersedia terpisah, dengan evaluasi anomali suntikan. Model untuk integrasi akhir masih menunggu pilihan pengguna.

Dataset/model tersebut tidak mempunyai kekeruhan; label proksi berasal dari aturan pH/suhu, bukan ahli atau kesehatan ikan. Source prediksi memerlukan pH/suhu interval sebelumnya dan riwayat yang cukup. Karena sensor pH belum ada dan TDS belum terintegrasi/terkalibrasi, inferensi lapangan model historis belum siap. Eksperimen offline tetap dapat ditinjau dengan datasetnya. Pelatihan ulang dengan fitur berbeda merupakan pekerjaan baru yang perlu evaluasi tersendiri.

## 5. Kebutuhan fungsional

Prioritas Core adalah perilaku produk yang dipertahankan dari baseline; Block adalah pekerjaan teknis lintas integrasi; Stretch menyatakan prioritas lanjutan yang sudah ada. Observasi manual tetap kebutuhan Core meskipun merupakan alur pendamping. Implementasi target dan hasil uji yang tersedia dipisahkan pada bagian 9.

| ID | Fungsi | Prioritas | Kriteria penerimaan |
| --- | --- | --- | --- |
| V3-FR01 | Autentikasi dan hak akses | Core | Login/logout bekerja; identitas/ownership diperiksa server; admin/viewer mempunyai batas mutasi yang diuji; password/token tidak muncul di log/respons. |
| V3-FR02 | Identitas dan status perangkat | Core, IoT | Perangkat satu kolam, heartbeat, umur koneksi dan credential dapat dikelola sesuai izin. Online tidak berarti reading baru atau sensor terkalibrasi. |
| V3-FR03 | Ingest dan persistensi telemetry | Core, IoT | Perangkat terautentikasi; payload/satuan/timestamp valid; UTC berzona, device ID, provenance serta kalibrasi disimpan. Retry identik idempotent; payload berbeda pada timestamp sama konflik. Raw/relatif, TDS diagnostik dan pH kosong tidak dipalsukan menjadi NTU/pH air valid. |
| V3-FR04 | Monitoring dan histori kolam | Core | Nilai/satuan/waktu/sumber/kalibrasi terlihat; histori dapat difilter; grafik tidak memberi nol pada null. Loading, kosong, error, stale, offline dan simulasi mempunyai state. |
| V3-FR05 | Ambang dan rekomendasi aturan | Core | Admin membaca/mengubah konfigurasi valid dengan snapshot/audit; hanya parameter/sumber yang memenuhi policy dievaluasi. Rekomendasi menjelaskan alasan; data kurang tidak menghasilkan kesimpulan kualitas air normal. |
| V3-FR06 | Peringatan dan tindak lanjut | Core | Breach valid membuat alert/log tanpa duplikat retry; parameter, nilai, ambang, sumber dan waktu dapat ditinjau. Acknowledge menyimpan aktor/waktu tanpa menyatakan air sudah pulih. Target notifikasi maksimal 60 detik setelah ingest valid diuji. |
| V3-FR07 | Kontrol manual dan histori aktuator | Core, IoT | Admin meminta command idempotent dengan channel/gate; pending/delivered/terminal serta histori ditampilkan. ACK dipisahkan dari hasil fisik. Pompa memakai kontrak/adapter eksplisit; tidak menyamar sebagai aerator. |
| V3-FR08 | Jadwal pakan dan log eksekusi | Core, IoT | Jadwal memakai zona waktu eksplisit; satu occurrence membuat satu command, tanpa backfill otomatis setelah restart. Sukses/gagal/timeout tercatat; simulasi tidak mengaktifkan jadwal fisik. Mekanisme SG90/dosis belum dianggap teruji. |
| V3-FR09 | Pipeline dan evaluasi ML offline | Block, ML | Tujuan/label/horizon dan dataset memiliki sumber; fitur historis kausal serta preprocessing training terdokumentasi. Split waktu, baseline, macro F1/balanced accuracy/recall/FP/FN dan batas label ditinjau dari output. Artefak, versi/hash, feature schema dan dependensi tidak tertukar antar eksperimen. |
| V3-FR10 | Inferensi dan penyajian prediksi ML | Block, integrasi | Adapter tervalidasi menggunakan pipeline terpilih serta input yang cocok. Hasil memiliki input window, sumber, model/version/hash dan waktu target. Data/history kurang, stale, timeout atau schema/model tidak cocok menghasilkan status belum tersedia. Prediksi tidak menjadi reading, alarm terukur atau command otomatis. |
| V3-FR11 | Audit operasi | Core | Mutasi ambang, jadwal, command serta credential memiliki who/what/when/resource yang konsisten dengan transaksi. Secret disensor; histori tidak dapat diubah melalui API pembaca. |
| V3-FR12 | Akses antarmuka web/PWA dan mobile | Core web, Block mobile | Web responsif dan PWA mempunyai manifest/service worker serta pengujian instalasi/cache. Flutter tetap deliverable dengan target platform dipilih, kontrak API serta state/role yang sama; client dan build belum diklaim selesai dari pemasangan SDK. |
| V3-FR13 | Observasi manual | Core, pendamping | Catatan tanggal/angka/teks divalidasi; pencatat dan provenance manual disimpan serta dapat ditinjau. Tidak dianggap pertumbuhan otomatis dari telemetry atau hasil ML. |
| V3-FR14 | Laporan dan ekspor operasional | Stretch | Periode berzona, agregasi data valid dan sumber terlihat; CSV/JSON mempertahankan filter/ownership/provenance. Teks CSV dinetralkan dari formula. Fitur ini bukan laporan Penulisan Ilmiah atau laporan bisnis. |

Kriteria pada satu kelompok FR dapat menjadi beberapa test case. Pengelompokan tidak menghapus pemeriksaan login, role, duplikat, timeout atau kegagalan sensor.

**Pemetaan ke dokumen implementasi Flask** (PRD/SRS/Arsitektur/Desain AquaSmart v1, 10 Okt 2026): V3-FR01→FR-001..005, V3-FR02→FR-008..012, V3-FR03→FR-013..015, V3-FR04→FR-015, V3-FR05→FR-007/025/026, V3-FR06→FR-022/023, V3-FR07→FR-016..020, V3-FR08→FR-024, V3-FR11→FR-034, V3-FR12→dokumen Desain, V3-FR13→FR-027, V3-FR14→FR-021/028. V3-FR09/V3-FR10 (ML) di luar implementasi Flask tahap ini.

## 6. Kebutuhan nonfungsional

Lima belas sasaran kualitas lama tetap dipertahankan karena penghapusan matkul tidak menghapus keamanan, keandalan atau aksesibilitas. Nilai target bukan hasil pengukuran baru.

| ID | Sasaran | Cara membuktikan |
| --- | --- | --- |
| V3-NFR01 | TTFB API lokal <2 detik | Dataset/endpoint representatif, konfigurasi mesin dan distribusi waktu dicatat. |
| V3-NFR02 | Uptime lokal >=90% | Jendela observasi/interval probe disepakati; health check tunggal tidak cukup. |
| V3-NFR03 | Akurasi pH +/-0,2 dan suhu +/-0,5 C | Alat referensi dan prosedur sesuai sensor; pH menunggu sensor fisik. Evaluasi ML bukan uji akurasi sensor. |
| V3-NFR04 | Hash password aman | Backend Flask memakai **bcrypt**; hash lama PHP `password_hash()` ($2y$) tetap dapat diverifikasi sehingga kredensial lama valid. Uji auth wajib lolos. |
| V3-NFR05 | TLS minimum 1.2 pada deployment | Sertifikat/transport client-perangkat diuji; HTTP loopback khusus pengembangan. |
| V3-NFR06 | Validasi input | Tipe, ukuran, rentang, nonfinite, timestamp, feature schema dan error konsisten diuji. |
| V3-NFR07 | Rate limit API publik | Pembatasan/Retry-After serta identitas client melalui proxy/BFF diuji. |
| V3-NFR08 | Mitigasi akses/injection/excessive data | Uji akses lintas owner, injection, mass assignment dan pencabutan hak sesuai kontrak. |
| V3-NFR09 | Kontrol aksesibel | Area sentuh pilihan proyek web 44x44 CSS px/Flutter 48 logical px, focus/keyboard/label serta pasangan kontras diuji; ukuran ini tidak dinyatakan sebagai batas WCAG yang sama. |
| V3-NFR10 | UI mobile-first dan reflow | Viewport, keyboard, zoom/text scaling, seluruh state dan preferensi reduced motion diuji. |
| V3-NFR11 | Tidak ada reading/command ganda | Retry dan ingest/command serentak diuji melalui constraint/transaksi dan idempotence. |
| V3-NFR12 | Retensi lokal minimal 6 bulan | Backup konsisten, restore serta pengamatan durasi; target jangka panjang tidak dianggap lulus dalam sesi praktikum. |
| V3-NFR13 | Dokumentasi kontrak | Method/path/auth/input/output/error, satuan/provenance serta schema inferensi tersedia; route usulan diberi label. |
| V3-NFR14 | Error dapat ditinjau | Fault injection, reference error, log tersensor dan rotasi log diuji; client tidak menerima SQL/token/traceback. |
| V3-NFR15 | Pemisahan sumber dan lingkungan | Simulasi/perangkat/manual/dataset ML dipisahkan dari ingest sampai grafik, alert, laporan, prediksi, ekspor serta audit. |

Reproduksibilitas/dependency manifest, validasi temporal dan batas label ML termasuk kriteria V3-FR09/V3-FR10; tidak dijadikan daftar FR baru untuk setiap teknik training.

## 7. Traceability tujuh matkul Block

Daftar berikut berasal dari jawaban pengguna. IoT tetap dihitung sebagai bagian Block proyek. Basis data dan web/PWA diperlukan sebagai komponen teknis, tetapi tidak ditambahkan sebagai matkul kedelapan/kesembilan.

| Matkul | Requirement/artefak | Batas |
| --- | --- | --- |
| Manajemen Proyek | Semua FR/NFR; SKPL, PRD, Architecture, Design, matriks transisi, backlog, risiko dan test evidence | Artefak teknis proyek dipertahankan; naskah Penulisan Ilmiah bukan gate. |
| Keamanan Siber | V3-FR01/V3-FR02/V3-FR11, V3-NFR04 sampai V3-NFR08; auth, ownership, device key, TLS, validasi dan audit | Klaim keamanan harus mempunyai hasil uji. |
| Komputasi Awan | Dockerfile/Compose, deployment/health, V3-NFR01/V3-NFR02/V3-NFR05/V3-NFR12 sampai V3-NFR14 | Docker praktikum teruji; cloud 24/7, uptime durasi dan restore tidak dianggap otomatis selesai. |
| Pemrograman BackEnd | V3-FR01 sampai V3-FR08, V3-FR11/V3-FR13/V3-FR14; REST, validasi, persistensi, diagram/ERD | **Backend produk kini Flask (Python)** menggantikan PHP 8 (keputusan 11 Okt 2026); kontrak API dipertahankan identik. |
| Aplikasi Mobile | V3-FR12 serta layar/state yang mengakses V3-FR01/V3-FR04 sampai V3-FR08/V3-FR10/V3-FR13/V3-FR14 | Flutter tetap masuk; web/PWA operasional tetap pendamping. SDK bukan bukti client/target Android selesai. |
| Python untuk Sistem Cerdas | V3-FR09/V3-FR10; notebook, pipeline, evaluasi/model card | Hasil offline dan inferensi produk dibedakan. |
| IoT | V3-FR02/V3-FR03/V3-FR07/V3-FR08; firmware/kalibrasi/test bench | Dihitung sebagai bagian Block proyek sesuai keputusan pengguna. |

## 8. Data, antarmuka dan artefak teknis

Domain mencakup pengguna/perangkat, reading/raw telemetry, aturan, alert, command/jadwal, audit, observasi manual dan laporan. Metadata/persistensi prediksi ML memerlukan kontrak tambahan sebelum implementasi. ERD/DDL akademik pada paket backend berisi 17 tabel serta satu view; bukan migrasi DB aktif dan tidak otomatis menjadi schema serving ML. Database runtime (demo.sqlite, 19 tabel) dipakai ulang oleh backend Flask tanpa migrasi.

Antarmuka utama: login, monitoring/histori, peringatan, kontrol, jadwal, pengaturan, profil dan laporan. Observasi manual mengikuti kontrak/UI yang perlu ditinjau. Layar memakai Bahasa Indonesia dan sumber/waktu/kalibrasi yang terlihat. Route yang sudah ada tidak membuktikan seluruh requirement telah diterapkan.

Artefak wajib teknis: kebutuhan/acceptance, Activity/Class/Sequence Diagram, ERD, desain stack Flask serta stack pendukung tiap fitur, kontrak API, model/feature metadata, prosedur pengujian serta bukti. Instalasi Flask/Flutter/Docker dicatat sebagai kesiapan toolchain, bukan tambahan FR. Architecture.MD dan Design.MD memerinci arsitektur dan interaksi; PRD.MD memerinci rencana produk. **SKPL V4.0 ini adalah baseline yang berlaku; bila dokumen pendamping tidak sepakat, SKPL yang menang.**

## 9. Verifikasi dan definisi selesai

| Tahap | Bukti tersedia | Gate yang belum ditutup |
| --- | --- | --- |
| Dokumentasi V4.0 | SKPL, tujuh matkul yang dikonfirmasi dan pemetaan transisi pada dokumen ini | Review/approval serta bukti penerimaan per requirement masih perlu dilengkapi. |
| Backend Flask (produk) | Implementasi Flask dengan kontrak API identik; 15/15 test kontrak hijau (11 Okt 2026) | FR Should/Could lanjutan, audit path, bukti deployment. |
| Frontend/mobile | Source web dan hasil uji historis; Flutter counter analyze/test/build web | Gate commit terkini, client Flutter AquaSmart serta Android/Windows sesuai target. |
| ML offline | Source/notebook, metadata evaluasi serta file model tersedia | Training tidak direrun di sesi ini; model terpilih, manifest/dependensi dan kriteria integrasi belum disepakati. |
| Inferensi ML | Rancangan adapter serta input/output terdokumentasi | Adapter/runtime belum dibuat; pH perangkat belum ada dan TDS belum terintegrasi. |
| IoT fisik | Inventaris dan rencana wadah dari pengguna; **tes hardware 10 Okt 2026: semua berhasil** (ESP32, turbidity, TDS, suhu, level, aktuator) | Kalibrasi formal sensor, dokumentasi hasil uji terukur. |
| Operasi | Target keamanan/performa/persistensi | Uptime/retensi berdurasi, restore dan UAT yang dapat ditinjau. |

Untuk setiap test case, catat ID requirement V3, sumber/commit, tanggal, lingkungan, input, hasil, evidence dan batas. Status yang digunakan: target, tersedia sebagian, lulus dengan bukti, atau belum terverifikasi. Kebutuhan fisik tidak lulus dari simulasi; kebutuhan ML tidak lulus dari keberadaan file model saja. Naskah ilmiah, game/3D dan bisnis tidak menjadi gate tambahan.

## 10. Matriks transisi dari baseline lama

Tabel ini mempertahankan jejak seluruh 24 FR lama. ID lama tidak dipakai untuk menilai baseline baru tanpa pemetaan.

| ID lama | Keputusan V4.0 | ID/lokasi baru |
| --- | --- | --- |
| FR1 | Dipertahankan; ingestion menjadi satu alur dengan persistensi | V3-FR03 |
| FR2 | Digabung ke alur telemetry | V3-FR03 |
| FR3 | Dipertahankan | V3-FR04 |
| FR4 | Digabung ke pengelolaan/evaluasi ambang | V3-FR05 |
| FR5 | Digabung ke lifecycle alert | V3-FR06 |
| FR6 | Digabung ke lifecycle alert | V3-FR06 |
| FR7 | Dipertahankan | V3-FR08 |
| FR8 | Log pakan dipertahankan bersama jadwal; histori terminal juga bagian kontrol | V3-FR08, V3-FR07 |
| FR9 | Dipertahankan; kontrak pompa harus eksplisit | V3-FR07 |
| FR10 | Rekomendasi aturan dipertahankan, prediksi ML dipisahkan | V3-FR05 |
| FR11 | Observasi operasional tetap dipertahankan | V3-FR13 |
| FR12 | Digabung dengan kontrol/histori | V3-FR07 |
| FR13 | Digabung dengan role/akses | V3-FR01 |
| FR14 | Digabung dengan auth/akses | V3-FR01 |
| FR15 | Digabung dengan konfigurasi/evaluasi ambang | V3-FR05 |
| FR16 | Digabung dengan konfigurasi/evaluasi ambang | V3-FR05 |
| FR17 | Digabung dengan identitas/status perangkat | V3-FR02 |
| FR18 | Digabung dengan identitas/status perangkat | V3-FR02 |
| FR19 | Snapshot aturan ada pada V3-FR05; metadata minimum model wajib untuk ML; UI registry lengkap tetap pengembangan lanjutan | V3-FR05, V3-FR09, V3-FR10 |
| FR20 | Laporan data kolam tetap stretch; tidak dianggap naskah ilmiah | V3-FR14 |
| FR21 | Ekspor operasional tetap stretch | V3-FR14 |
| FR22 | Dipindahkan ke artefak desain operasional; tidak dihitung sebagai fungsi runtime | Bagian 8, Design.MD |
| FR23 | PWA dipertahankan; Flutter tetap deliverable mobile | V3-FR12 |
| FR24 | Dipertahankan | V3-FR11 |
| ML-01 | Tujuan/data/feature schema | V3-FR09 |
| ML-02 | Pipeline serta metadata artefak | V3-FR09, V3-FR10 |
| ML-03 | Evaluasi ML offline | V3-FR09 |
| ML-04 | Inferensi/presentasi dan state kegagalan | V3-FR10 |
| FR25/FR26 pada RTM historis | Tidak ada pada tabel FR SKPL lama; atribusi Penulisan Ilmiah dikeluarkan | Di luar baseline V4.0 |

NFR1 sampai NFR15 lama dipetakan satu per satu ke V3-NFR01 sampai V3-NFR15. Kontribusi Multimedia Interaktif dan Kewirausahaan tidak mempunyai ID eksplisit pada tabel 24 FR sumber; V3.0 mengecualikan kontribusinya berdasarkan keputusan pengguna, tanpa mengarang FR lama untuk keduanya.

## 11. Pertanyaan terbuka

- Fokus platform Flutter serta client yang diutamakan untuk demonstrasi.
- Model ML yang dipilih untuk integrasi: prediksi status, anomali, atau target lain.
- Varian/probe/rating perangkat, dimensi dalam/volume efektif dan rencana daya/driver.
- Rubrik/format/tenggat, kewajiban HTML/CSS slide 22 dan pihak yang menyetujui kebutuhan/ambang.

## 12. Sumber dan dokumen pendamping

- Keputusan pengguna 5 Oktober 2026: V3.0, pengecualian tiga matkul, tujuh matkul pada bagian 7, IoT masuk Block dan seluruh komponen teknis sebelumnya tetap digunakan.
- **Keputusan pengguna 11 Oktober 2026: backend produk diganti PHP 8 → Flask (Python); SKPL direvisi ke V4.0.**
- SKPL V3.0 historis serta RTM historis: sumber transisi; bukan baseline penilaian V4.0.
- README produk, panduan satu kolam, API aktif dan CR-001: runtime dan batas kontrak.
- ML Hari 1, ML Hari 2 dan source pipeline: ML offline serta syarat input.
- Audit praktikum/tugas: bukti toolchain/praktikum historis.
- PRD/SRS/Architecture/Design AquaSmart v1 (10 Okt 2026): dokumen implementasi Flask; selaras dengan SKPL V4.0 (SKPL menang bila tidak sepakat).
