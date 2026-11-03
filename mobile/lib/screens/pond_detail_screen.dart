import 'dart:async';

import 'package:flutter/material.dart';

import '../api.dart';
import '../format.dart';
import '../theme.dart';
import '../widgets/reading_chart.dart';
import '../widgets/states.dart';

const _statusPerintah = {
  'pending': 'Antre',
  'delivered': 'Terkirim',
  'succeeded': 'Berhasil',
  'failed': 'Gagal',
  'timeout': 'Tanpa balasan',
};

const _namaAktuator = {'aerator': 'Aerator', 'feeder': 'Pakan'};

/// The backend stops treating a pending or delivered command as busy once
/// `expires_at` passes, but only its optional scheduler rewrites the status,
/// so the app decides from the timestamp. Uses the phone clock.
bool _kedaluwarsa(Command c) =>
    (c.status == 'pending' || c.status == 'delivered') &&
    c.expiresAt != null &&
    DateTime.now().millisecondsSinceEpoch ~/ 1000 > c.expiresAt!;

class PondDetailScreen extends StatefulWidget {
  const PondDetailScreen({
    super.key,
    required this.api,
    required this.device,
    required this.thresholds,
    required this.onSessionLost,
  });

  final ApiClient api;
  final Device device;
  final Thresholds thresholds;
  final VoidCallback onSessionLost;

  @override
  State<PondDetailScreen> createState() => _PondDetailScreenState();
}

class _Data {
  _Data(this.device, this.readings, this.commands);

  final Device device;
  final List<Reading> readings;
  final List<Command> commands;
}

class _PondDetailScreenState extends State<PondDetailScreen>
    with WidgetsBindingObserver {
  late Future<_Data> _load = _fetch();
  // Kept so a failed refresh leaves the last good readings and controls up.
  _Data? _last;
  DateTime? _lastAt;
  bool _sessionLost = false;
  Parameter _param = Parameter.ph;
  String? _sending;
  String? _controlError;
  int _durasi = 5;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _startPolling();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    super.dispose();
  }

  // Same cadence as the web control page, so a firmware ack shows up
  // without the user having to refresh.
  void _startPolling() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 10), (_) {
      if (_sending == null) _refresh();
    });
  }

  // A locked phone or a minimised app should not spend data and battery
  // on three requests every 10 seconds.
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (_sessionLost) return;
    switch (state) {
      case AppLifecycleState.resumed:
        _refresh();
        _startPolling();
      case AppLifecycleState.paused:
      case AppLifecycleState.hidden:
      case AppLifecycleState.detached:
        _timer?.cancel();
        _timer = null;
      case AppLifecycleState.inactive:
        break;
    }
  }

  Future<_Data> _fetch() async {
    try {
      final devices = await widget.api.devices();
      final device = devices.firstWhere(
        (d) => d.id == widget.device.id,
        orElse: () => widget.device,
      );
      final data = _Data(
        device,
        await widget.api.readings(device.id),
        await widget.api.commands(device.id),
      );
      _last = data;
      _lastAt = DateTime.now();
      return data;
    } on ApiException catch (e) {
      if (e.status == 401) _endSession();
      rethrow;
    }
  }

  void _endSession() {
    if (_sessionLost || !mounted) return;
    _sessionLost = true;
    _timer?.cancel();
    _timer = null;
    widget.onSessionLost();
  }

  Future<void> _refresh() async {
    if (_sessionLost || !mounted) return;
    final f = _fetch();
    setState(() {
      _load = f;
    });
    await f.then((_) {}, onError: (_) {});
  }

  Future<void> _send(String actuator, bool value, {int? duration}) async {
    setState(() {
      _sending = actuator;
      _controlError = null;
    });
    try {
      await widget.api.control(
        widget.device.id,
        actuator,
        value,
        duration: duration,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            actuator == 'auto'
                ? 'Mode otomatis ${value ? 'dinyalakan' : 'dimatikan'}.'
                : 'Perintah masuk antrian. Status berubah setelah perangkat melapor.',
          ),
        ),
      );
      await _refresh();
    } on ApiException catch (e) {
      if (e.status == 401) {
        _endSession();
        return;
      }
      setState(
        () => _controlError = e.status == 409
            ? 'Masih ada perintah ${_namaAktuator[actuator]?.toLowerCase() ?? actuator} '
                  'yang belum selesai. Tunggu laporan perangkat, lalu coba lagi.'
            : e.message,
      );
    } finally {
      if (mounted) setState(() => _sending = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.device.name),
        actions: [
          IconButton(
            tooltip: 'Muat ulang',
            onPressed: _refresh,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder(
          future: _load,
          builder: (context, snap) {
            final d = snap.data ?? _last;
            if (snap.connectionState != ConnectionState.done && d == null) {
              return const LoadingView('Memuat bacaan dan perintah...');
            }
            if (d == null) {
              return MessageView(
                title: 'Data kolam gagal dimuat',
                body: '${snap.error}',
                actionLabel: 'Coba lagi',
                onAction: _refresh,
                isError: true,
              );
            }
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 32),
              children: [
                if (snap.hasError && !_sessionLost) ...[
                  _gagalPerbarui(snap.error!),
                  const SizedBox(height: 12),
                ],
                _header(d.device),
                const SizedBox(height: 20),
                _terkini(d.device),
                const SizedBox(height: 28),
                _riwayat(d.readings),
                const SizedBox(height: 28),
                _kontrol(d.device, d.commands),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _gagalPerbarui(Object error) => Semantics(
    container: true,
    liveRegion: true,
    child: Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Palette.soft,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        'Pembaruan gagal, data per '
        '${_lastAt == null ? '-' : formatWaktu(_lastAt!)}. $error',
        style: Theme.of(
          context,
        ).textTheme.bodySmall?.copyWith(color: Palette.alarmCoralText),
      ),
    ),
  );

  Widget _header(Device d) => Text(
    '${d.location} · ${labelKoneksi(d.online)} · '
    'terakhir terlihat ${formatIso(d.lastSeen)}',
    style: const TextStyle(color: Palette.muted),
  );

  Widget _judul(String t) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Text(t, style: Theme.of(context).textTheme.titleMedium),
  );

  Widget _terkini(Device d) {
    final r = d.latest;
    if (r == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text(
            'Belum ada bacaan dari perangkat ini. Bacaan muncul setelah perangkat '
            'mengirim data ke server.',
          ),
        ),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _judul('Bacaan terakhir'),
        Card(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: Column(
              children: [
                for (final p in Parameter.semua) ...[
                  _BarisParameter(p: p, r: r, t: widget.thresholds),
                  if (p != Parameter.semua.last) const Divider(),
                ],
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    '${formatIso(r.time)} · ${labelSumber(r)}',
                    style: Theme.of(
                      context,
                    ).textTheme.labelSmall?.copyWith(color: Palette.muted),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _riwayat(List<Reading> readings) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _judul('Riwayat bacaan'),
        SegmentedButton<Parameter>(
          segments: [
            for (final p in Parameter.semua)
              ButtonSegment(value: p, label: Text(p.label)),
          ],
          selected: {_param},
          showSelectedIcon: false,
          onSelectionChanged: (s) => setState(() => _param = s.first),
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: readings.isEmpty
                ? const Text('Belum ada bacaan untuk digambar.')
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${_param.label} di ${readings.length} bacaan terakhir. '
                        'Pita hijau muda adalah batas aman (${_param.teksBatas(widget.thresholds)}); '
                        'titik oranye berada di luar batas.',
                        style: Theme.of(
                          context,
                        ).textTheme.bodySmall?.copyWith(color: Palette.muted),
                      ),
                      const SizedBox(height: 12),
                      ReadingChart(
                        readings: readings,
                        parameter: _param,
                        thresholds: widget.thresholds,
                      ),
                    ],
                  ),
          ),
        ),
      ],
    );
  }

  Widget _kontrol(Device d, List<Command> commands) {
    final admin = widget.api.user?.isAdmin ?? false;
    final busy = _sending != null;
    final tt = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _judul('Kontrol'),
        // Same wording as the web ControlNotice: a "Berhasil" status must not
        // read as proof that a motor moved.
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Palette.soft,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Aktuasi fisik belum terbukti',
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: Palette.sedimentText,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Perintah disimpan server lalu diambil ESP32, tetapi hanya bila feeder '
                'atau relay diaktifkan di konfigurasi firmware. Status Berhasil berarti '
                'firmware melaporkan keluarannya sudah diubah, bukan bukti relay atau '
                'motor bergerak.',
                style: tt.bodySmall,
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        if (!admin)
          const Padding(
            padding: EdgeInsets.only(bottom: 12),
            child: Text(
              'Akun ini hanya bisa melihat status. Perintah hanya bisa '
              'dikirim admin.',
            ),
          ),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _Aktuator(
                  nama: 'Aerator',
                  keterangan: 'Menambah sirkulasi dan oksigen di air kolam.',
                  menyala: d.aerator,
                ),
                if (admin) ...[
                  const SizedBox(height: 10),
                  FilledButton(
                    onPressed: busy ? null : () => _send('aerator', !d.aerator),
                    child: Text(
                      _sending == 'aerator'
                          ? 'Mengirim perintah...'
                          : '${d.aerator ? 'Matikan' : 'Nyalakan'} aerator',
                    ),
                  ),
                ],
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 16),
                  child: Divider(),
                ),
                Text('Pakan', style: tt.titleSmall),
                const SizedBox(height: 2),
                const Text(
                  'Memberi pakan satu kali selama durasi yang dipilih.',
                  style: TextStyle(color: Palette.muted),
                ),
                if (admin) ...[
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      const Text('Durasi'),
                      const Spacer(),
                      IconButton.outlined(
                        tooltip: 'Kurangi durasi',
                        onPressed: _durasi > 1
                            ? () => setState(() => _durasi--)
                            : null,
                        icon: const Icon(Icons.remove),
                      ),
                      SizedBox(
                        width: 72,
                        child: Text(
                          '$_durasi detik',
                          textAlign: TextAlign.center,
                          style: dataStyle.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      IconButton.outlined(
                        tooltip: 'Tambah durasi',
                        onPressed: _durasi < 10
                            ? () => setState(() => _durasi++)
                            : null,
                        icon: const Icon(Icons.add),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  FilledButton(
                    onPressed: busy
                        ? null
                        : () => _send('feeder', true, duration: _durasi),
                    child: Text(
                      _sending == 'feeder'
                          ? 'Mengirim perintah...'
                          : 'Beri pakan sekarang',
                    ),
                  ),
                ],
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 16),
                  child: Divider(),
                ),
                _Aktuator(
                  nama: 'Mode otomatis',
                  keterangan:
                      'Status ini disimpan server. Backend belum menjalankan '
                      'jadwal pakan secara otomatis.',
                  menyala: d.auto,
                ),
                if (admin) ...[
                  const SizedBox(height: 10),
                  OutlinedButton(
                    onPressed: busy ? null : () => _send('auto', !d.auto),
                    child: Text(
                      _sending == 'auto'
                          ? 'Menyimpan...'
                          : '${d.auto ? 'Matikan' : 'Nyalakan'} mode otomatis',
                    ),
                  ),
                ],
                if (_controlError != null) ...[
                  const SizedBox(height: 12),
                  Semantics(
                    container: true,
                    liveRegion: true,
                    child: Text(
                      _controlError!,
                      key: const Key('control-error'),
                      style: const TextStyle(color: Palette.alarmCoralText),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        _judul('Perintah terakhir'),
        if (commands.isEmpty)
          const Text(
            'Belum ada perintah untuk perangkat ini.',
            style: TextStyle(color: Palette.muted),
          )
        else
          Card(
            child: Column(
              children: [
                for (final c in commands.take(5))
                  ListTile(
                    title: Text(
                      c.actuator == 'feeder'
                          ? 'Pakan ${c.duration} detik'
                          : '${_namaAktuator[c.actuator] ?? c.actuator} '
                                '${c.value ? 'nyala' : 'mati'}',
                    ),
                    subtitle: Text(formatEpoch(c.createdAt)),
                    trailing: Text(
                      _kedaluwarsa(c)
                          ? 'Kedaluwarsa'
                          : _statusPerintah[c.status] ?? c.status,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: c.status == 'succeeded'
                            ? Palette.clearWaterText
                            : c.status == 'failed' ||
                                  c.status == 'timeout' ||
                                  _kedaluwarsa(c)
                            ? Palette.alarmCoralText
                            : Palette.muted,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        const SizedBox(height: 8),
        Text(
          'Antre: menunggu diambil perangkat. Terkirim: sudah diambil ESP32. '
          'Berhasil atau Gagal: laporan firmware. Kedaluwarsa: perangkat tidak '
          'melapor sebelum batas waktu perintah lewat. Layar ini diperbarui '
          'otomatis setiap 10 detik selama aplikasi terbuka.',
          style: tt.labelSmall?.copyWith(color: Palette.muted),
        ),
      ],
    );
  }
}

class _BarisParameter extends StatelessWidget {
  const _BarisParameter({required this.p, required this.r, required this.t});

  final Parameter p;
  final Reading r;
  final Thresholds t;

  @override
  Widget build(BuildContext context) {
    final k = p.kondisi(r, t);
    final tt = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  p.label,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                Text(
                  'Batas aman ${p.teksBatas(t)}',
                  style: tt.labelSmall?.copyWith(color: Palette.muted),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${formatAngka(p.of(r))}${p.unit.isEmpty ? '' : ' ${p.unit}'}',
                style: tt.headlineSmall
                    ?.merge(dataStyle)
                    .copyWith(fontWeight: FontWeight.w600, letterSpacing: 0),
              ),
              Text(
                teksKondisi(k),
                style: tt.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: warnaKondisi(k),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Aktuator extends StatelessWidget {
  const _Aktuator({
    required this.nama,
    required this.keterangan,
    required this.menyala,
  });

  final String nama;
  final String keterangan;
  final bool menyala;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Row(
        children: [
          Expanded(
            child: Text(nama, style: Theme.of(context).textTheme.titleSmall),
          ),
          Text(
            menyala ? 'Tercatat menyala' : 'Tercatat mati',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: menyala ? Palette.clearWaterText : Palette.muted,
            ),
          ),
        ],
      ),
      const SizedBox(height: 2),
      Text(keterangan, style: const TextStyle(color: Palette.muted)),
    ],
  );
}
