import 'package:flutter/material.dart';

/// FrontEnd/public/logo.svg redrawn as paths, so the app needs no SVG package.
class LogoMark extends StatelessWidget {
  const LogoMark({super.key, this.size = 40});

  final double size;

  @override
  Widget build(BuildContext context) => Semantics(
    label: 'Logo AquaSmart',
    child: CustomPaint(size: Size.square(size), painter: _LogoPainter()),
  );
}

class _LogoPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    canvas.scale(size.width / 128);
    final drop = Path()
      ..moveTo(64, 8)
      ..cubicTo(51, 29, 27, 54, 27, 79)
      ..cubicTo(27, 101, 43.6, 119, 64, 119)
      ..cubicTo(84.4, 119, 101, 101, 101, 79)
      ..cubicTo(101, 54, 77, 29, 64, 8)
      ..close();
    canvas.drawPath(drop, Paint()..color = const Color(0xFFF1F5F3));
    canvas.drawPath(
      drop,
      Paint()
        ..color = const Color(0xFFD8E2DE)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 4,
    );
    final line = Paint()
      ..color = const Color(0xFF0E2A30)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6
      ..strokeCap = StrokeCap.square;
    canvas.drawLine(const Offset(42, 74), const Offset(86, 74), line);
    canvas.drawLine(const Offset(42, 88), const Offset(72, 88), line);
    canvas.drawLine(const Offset(52, 48), const Offset(76, 48), line);
    canvas.drawLine(const Offset(64, 36), const Offset(64, 60), line);
    canvas.drawCircle(
      const Offset(84, 88),
      5,
      Paint()..color = const Color(0xFF10262A),
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
