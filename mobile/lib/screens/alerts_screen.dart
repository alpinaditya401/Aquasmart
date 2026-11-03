import 'package:flutter/material.dart';

import '../api.dart';
import '../format.dart';
import '../theme.dart';
import '../widgets/states.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({
    super.key,
    required this.api,
    required this.pondNames,
    required this.onCount,
    required this.onSessionLost,
  });

  final ApiClient api;

  /// Device serial to pond name, from the ponds tab; the serial is shown
  /// until that list has loaded.
  final Map<String, String> pondNames;
  final ValueChanged<int> onCount;
  final VoidCallback onSessionLost;

  @override
  State<AlertsScreen> createState() => AlertsScreenState();
}

class AlertsScreenState extends State<AlertsScreen> {
  late Future<List<Alert>> _load = _fetch();
  final Set<int> _busy = {};

  Future<List<Alert>> _fetch() async {
    final (list, unread) = await widget.api.alerts();
    widget.onCount(unread);
    return list;
  }

  Future<void> refresh() async {
    final f = _fetch();
    setState(() {
      _load = f;
    });
    await f.then((_) {}, onError: (_) {});
  }

  Future<void> _ack(Alert a) async {
    setState(() => _busy.add(a.id));
    try {
      await widget.api.acknowledge(a.id);
    } on ApiException catch (e) {
      // 409: someone already marked it read, which is the state we wanted.
      if (e.status != 409 && mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    } finally {
      _busy.remove(a.id);
    }
    await refresh();
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: refresh,
      child: FutureBuilder(
        future: _load,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done && !snap.hasData) {
            return const LoadingView('Memuat peringatan...');
          }
          if (snap.hasError) {
            final e = snap.error;
            if (e is ApiException && e.status == 401) {
              WidgetsBinding.instance.addPostFrameCallback(
                (_) => widget.onSessionLost(),
              );
            }
            return MessageView(
              title: 'Peringatan gagal dimuat',
              body: '$e',
              actionLabel: 'Coba lagi',
              onAction: refresh,
              isError: true,
            );
          }
          final alerts = snap.data!;
          if (alerts.isEmpty) {
            return const MessageView(
              title: 'Tidak ada peringatan',
              body:
                  'Peringatan muncul saat bacaan pH, suhu, atau kekeruhan baru keluar '
                  'dari batas aman kolam Anda.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            itemCount: alerts.length,
            separatorBuilder: (_, _) => const SizedBox(height: 10),
            itemBuilder: (context, i) {
              final a = alerts[i];
              final meta = Theme.of(
                context,
              ).textTheme.labelSmall?.copyWith(color: Palette.muted);
              return Card(
                color: a.acknowledged ? Palette.foam : Palette.surfaceWhite,
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '${widget.pondNames[a.deviceId] ?? a.deviceId} · '
                              '${formatIso(a.createdAt)}',
                              style: meta,
                            ),
                          ),
                          Text(
                            a.acknowledged ? 'Sudah dibaca' : 'Belum dibaca',
                            style: meta?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: a.acknowledged
                                  ? Palette.muted
                                  : Palette.alarmCoralText,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(a.message, style: const TextStyle(height: 1.4)),
                      // The raw `source` is an uppercase backend label; the
                      // reading cards word provenance this way.
                      if (a.provenance.isNotEmpty) ...[
                        const SizedBox(height: 6),
                        Text(
                          'Sumber: ${labelProvenance(a.provenance)}',
                          style: meta,
                        ),
                      ],
                      if (!a.acknowledged) ...[
                        const SizedBox(height: 10),
                        OutlinedButton(
                          onPressed: _busy.contains(a.id)
                              ? null
                              : () => _ack(a),
                          child: Text(
                            _busy.contains(a.id)
                                ? 'Menyimpan...'
                                : 'Tandai sudah dibaca',
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
