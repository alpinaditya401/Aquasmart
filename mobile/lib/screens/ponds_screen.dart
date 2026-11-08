import 'package:flutter/material.dart';

import '../api.dart';
import '../format.dart';
import '../theme.dart';
import '../widgets/states.dart';
import 'pond_detail_screen.dart';

class PondsScreen extends StatefulWidget {
  const PondsScreen({
    super.key,
    required this.api,
    required this.onDevices,
    required this.onSessionLost,
  });

  final ApiClient api;
  final ValueChanged<List<Device>> onDevices;
  final VoidCallback onSessionLost;

  @override
  State<PondsScreen> createState() => PondsScreenState();
}

class PondsScreenState extends State<PondsScreen> {
  late Future<(List<Device>, Thresholds)> _load = _fetch();

  Future<(List<Device>, Thresholds)> _fetch() async {
    final devices = await widget.api.devices();
    if (mounted) widget.onDevices(devices);
    return (devices, await widget.api.thresholds());
  }

  Future<void> refresh() async {
    final f = _fetch();
    setState(() {
      _load = f;
    });
    await f.then((_) {}, onError: (_) {});
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: refresh,
      child: FutureBuilder(
        future: _load,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done && !snap.hasData) {
            return const LoadingView('Memuat data kolam...');
          }
          if (snap.hasError) {
            final e = snap.error;
            if (e is ApiException && e.status == 401) {
              WidgetsBinding.instance.addPostFrameCallback(
                (_) => widget.onSessionLost(),
              );
            }
            return MessageView(
              title: 'Data kolam gagal dimuat',
              body: '$e',
              actionLabel: 'Coba lagi',
              onAction: refresh,
              isError: true,
            );
          }
          final (devices, t) = snap.data!;
          if (devices.isEmpty) {
            return const MessageView(
              title: 'Belum ada kolam',
              body:
                  'Akun ini belum punya perangkat. Klaim perangkat dengan nomor seri '
                  'lewat dashboard web AquaSmart, lalu tekan Muat ulang di kanan atas.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            itemCount: devices.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) => _PondCard(
              device: devices[i],
              thresholds: t,
              onTap: () async {
                await Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => PondDetailScreen(
                      api: widget.api,
                      device: devices[i],
                      thresholds: t,
                      onSessionLost: widget.onSessionLost,
                    ),
                  ),
                );
                if (mounted) refresh();
              },
            ),
          );
        },
      ),
    );
  }
}

class _PondCard extends StatelessWidget {
  const _PondCard({
    required this.device,
    required this.thresholds,
    required this.onTap,
  });

  final Device device;
  final Thresholds thresholds;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final r = device.latest;
    final keluar = r == null
        ? <Parameter>[]
        : Parameter.semua
              .where((p) => p.kondisi(r, thresholds) == Kondisi.diLuarBatas)
              .toList();
    final ringkas = r == null
        ? 'Belum ada bacaan'
        : keluar.isEmpty
        ? 'Semua parameter aman'
        : '${keluar.map((p) => p.label).join(', ')} di luar batas';

    final tt = Theme.of(context).textTheme;
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(child: Text(device.name, style: tt.titleMedium)),
                  Text(
                    labelKoneksi(device.online),
                    style: tt.bodySmall?.copyWith(
                      fontWeight: FontWeight.w600,
                      color: device.online
                          ? Palette.clearWaterText
                          : Palette.muted,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 2),
              Text(
                device.location,
                style: const TextStyle(color: Palette.muted),
              ),
              const SizedBox(height: 12),
              Text(
                ringkas,
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: r == null
                      ? Palette.muted
                      : keluar.isEmpty
                      ? Palette.clearWaterText
                      : Palette.alarmCoralText,
                ),
              ),
              if (r != null) ...[
                const SizedBox(height: 10),
                Row(
                  children: [
                    for (final p in Parameter.semua)
                      Expanded(
                        child: _Nilai(p: p, r: r, t: thresholds),
                      ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  '${formatIso(r.time)} · ${labelSumber(r)}',
                  style: tt.labelSmall?.copyWith(color: Palette.muted),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _Nilai extends StatelessWidget {
  const _Nilai({required this.p, required this.r, required this.t});

  final Parameter p;
  final Reading r;
  final Thresholds t;

  @override
  Widget build(BuildContext context) {
    final k = p.kondisi(r, t);
    final tt = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(p.label, style: tt.labelSmall?.copyWith(color: Palette.muted)),
        Text(
          '${formatAngka(p.of(r))}${p.unit.isEmpty ? '' : ' ${p.unit}'}',
          style: tt.titleMedium?.merge(dataStyle).copyWith(
            color: warnaKondisi(k),
          ),
        ),
      ],
    );
  }
}
