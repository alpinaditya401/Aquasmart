import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../api.dart';
import '../format.dart';
import '../theme.dart';

/// One parameter over the latest readings, with the owner's safe range drawn
/// as a band so a point outside it is visible without reading numbers.
class ReadingChart extends StatelessWidget {
  const ReadingChart({
    super.key,
    required this.readings,
    required this.parameter,
    required this.thresholds,
  });

  final List<Reading> readings;
  final Parameter parameter;
  final Thresholds thresholds;

  @override
  Widget build(BuildContext context) {
    final values = readings.map(parameter.of).toList();
    final (lo, hi) = parameter.batas(thresholds);
    final minV = math.min(values.reduce(math.min), lo);
    final maxV = math.max(values.reduce(math.max), hi);
    final pad = (maxV - minV) == 0 ? 1.0 : (maxV - minV) * 0.12;
    final yMin = minV - pad;
    final yMax = maxV + pad;
    final keluar = readings
        .where((r) => parameter.kondisi(r, thresholds) == Kondisi.diLuarBatas)
        .length;
    final unit = parameter.unit.isEmpty ? '' : ' ${parameter.unit}';

    return Semantics(
      label:
          '${parameter.label}, ${readings.length} bacaan terakhir, '
          '$keluar di luar batas. Terakhir ${formatAngka(values.last)}$unit.',
      child: ExcludeSemantics(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SizedBox(
              height: 180,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  SizedBox(
                    width: 40,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(formatAngka(yMax), style: _axis),
                        Text(formatAngka(yMin), style: _axis),
                      ],
                    ),
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: CustomPaint(
                      painter: _ChartPainter(values, yMin, yMax, lo, hi),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 4),
            Padding(
              padding: const EdgeInsets.only(left: 46),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(formatIso(readings.first.time), style: _axis),
                  Text(formatIso(readings.last.time), style: _axis),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

const _axis = TextStyle(fontSize: 11, color: Palette.muted);

class _ChartPainter extends CustomPainter {
  _ChartPainter(this.values, this.yMin, this.yMax, this.lo, this.hi);

  final List<double> values;
  final double yMin, yMax, lo, hi;

  double _y(double v, Size s) =>
      s.height - (v - yMin) / (yMax - yMin) * s.height;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(
      Rect.fromLTRB(0, _y(hi, size), size.width, _y(lo, size)),
      Paint()..color = Palette.soft,
    );
    final grid = Paint()
      ..color = Palette.foamLine
      ..strokeWidth = 1;
    canvas.drawLine(
      Offset(0, size.height),
      Offset(size.width, size.height),
      grid,
    );

    final dx = values.length == 1 ? 0.0 : size.width / (values.length - 1);
    final path = Path();
    for (var i = 0; i < values.length; i++) {
      final p = Offset(
        values.length == 1 ? size.width / 2 : i * dx,
        _y(values[i], size),
      );
      i == 0 ? path.moveTo(p.dx, p.dy) : path.lineTo(p.dx, p.dy);
    }
    canvas.drawPath(
      path,
      Paint()
        ..color = Palette.clearWaterText
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2,
    );
    for (var i = 0; i < values.length; i++) {
      final v = values[i];
      if (v >= lo && v <= hi) continue;
      final p = Offset(
        values.length == 1 ? size.width / 2 : i * dx,
        _y(v, size),
      );
      canvas.drawCircle(p, 4, Paint()..color = Palette.alarmCoral);
    }
  }

  @override
  bool shouldRepaint(covariant _ChartPainter old) =>
      old.values != values || old.lo != lo || old.hi != hi;
}
