import 'package:flutter/material.dart';

import 'api.dart';
import 'theme.dart';

const _bulan = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'Mei',
  'Jun',
  'Jul',
  'Agu',
  'Sep',
  'Okt',
  'Nov',
  'Des',
];

String _two(int n) => n.toString().padLeft(2, '0');

String formatWaktu(DateTime t) {
  final l = t.toLocal();
  return '${l.day} ${_bulan[l.month - 1]} ${_two(l.hour)}:${_two(l.minute)}';
}

/// ISO-8601 from the API; shown in the phone's local time.
String formatIso(String? iso) {
  if (iso == null || iso.isEmpty) return 'belum pernah';
  final t = DateTime.tryParse(iso);
  return t == null ? iso : formatWaktu(t);
}

String formatEpoch(int seconds) => formatWaktu(
  DateTime.fromMillisecondsSinceEpoch(seconds * 1000, isUtc: true),
);

String formatAngka(double v) =>
    v == v.roundToDouble() ? v.toStringAsFixed(0) : v.toStringAsFixed(1);

/// Where a reading came from, worded like the web dashboard's labels.
String labelSumber(Reading r) {
  if (r.simulation || r.provenance == 'simulation') return 'SIMULASI';
  if (r.provenance == 'device') {
    return 'Perangkat, kalibrasi belum diverifikasi';
  }
  return 'Data lama, belum diverifikasi';
}

enum Kondisi { aman, diLuarBatas }

class Parameter {
  const Parameter(this.key, this.label, this.unit);

  final String key;
  final String label;
  final String unit;

  static const ph = Parameter('ph', 'pH', '');
  static const suhu = Parameter('temperature', 'Suhu', '°C');
  static const kekeruhan = Parameter('turbidity', 'Kekeruhan', 'NTU');
  static const semua = [ph, suhu, kekeruhan];

  double of(Reading r) => switch (key) {
    'ph' => r.ph,
    'temperature' => r.temperature,
    _ => r.turbidity,
  };

  (double, double) batas(Thresholds t) => switch (key) {
    'ph' => (t.phMin, t.phMax),
    'temperature' => (t.temperatureMin, t.temperatureMax),
    _ => (0, t.turbidityMax),
  };

  Kondisi kondisi(Reading r, Thresholds t) {
    final (lo, hi) = batas(t);
    final v = of(r);
    return v < lo || v > hi ? Kondisi.diLuarBatas : Kondisi.aman;
  }

  String teksBatas(Thresholds t) {
    final (lo, hi) = batas(t);
    final u = unit.isEmpty ? '' : ' $unit';
    return key == 'turbidity'
        ? 'maks ${formatAngka(hi)}$u'
        : '${formatAngka(lo)} sampai ${formatAngka(hi)}$u';
  }
}

Color warnaKondisi(Kondisi k) =>
    k == Kondisi.aman ? Palette.clearWaterText : Palette.alarmCoralText;

String teksKondisi(Kondisi k) => k == Kondisi.aman ? 'Aman' : 'Di luar batas';
