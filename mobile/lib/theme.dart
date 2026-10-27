import 'package:flutter/material.dart';

/// Tokens from FrontEnd/DESIGN_SYSTEM.md, so the phone app reads as the same
/// product as the web dashboard. Light theme only, as on the web.
class Palette {
  static const ink = Color(0xFF193F3A);
  static const deepCurrent = Color(0xFF174C40);
  static const muted = Color(0xFF566B63);
  static const clearWaterText = Color(0xFF24624E);
  static const sedimentText = Color(0xFF7A4B1A);
  static const alarmCoralText = Color(0xFF9B3B09);
  static const foam = Color(0xFFF5F7F3);
  static const surfaceWhite = Color(0xFFFFFFFF);
  static const bgDeep = Color(0xFFE7EEE7);
  static const foamLine = Color(0xFFDCE5DD);
  static const soft = Color(0xFFEDF2E9);

  // Fill-only colours (not for text), as in the web design system.
  static const clearWater = Color(0xFF4C9A8E);
  static const alarmCoral = Color(0xFFD2601F);
}

ThemeData buildTheme() {
  const radiusControl = BorderRadius.all(Radius.circular(8));
  const radiusPanel = BorderRadius.all(Radius.circular(16));
  final base = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Palette.deepCurrent,
      primary: Palette.deepCurrent,
      onPrimary: Palette.surfaceWhite,
      surface: Palette.foam,
      onSurface: Palette.ink,
      error: Palette.alarmCoralText,
    ),
    scaffoldBackgroundColor: Palette.foam,
  );
  return base.copyWith(
    textTheme: base.textTheme.apply(
      bodyColor: Palette.ink,
      displayColor: Palette.ink,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Palette.foam,
      foregroundColor: Palette.ink,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        color: Palette.ink,
        fontSize: 20,
        fontWeight: FontWeight.w600,
      ),
    ),
    // Panels are flat on the dashboard; the line separates, not a shadow.
    cardTheme: const CardThemeData(
      color: Palette.surfaceWhite,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: radiusPanel,
        side: BorderSide(color: Palette.foamLine),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: Palette.deepCurrent,
        foregroundColor: Palette.surfaceWhite,
        minimumSize: const Size(48, 48),
        shape: const RoundedRectangleBorder(borderRadius: radiusControl),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Palette.deepCurrent,
        minimumSize: const Size(48, 48),
        side: const BorderSide(color: Palette.muted),
        shape: const RoundedRectangleBorder(borderRadius: radiusControl),
      ),
    ),
    inputDecorationTheme: const InputDecorationTheme(
      filled: true,
      fillColor: Palette.surfaceWhite,
      border: OutlineInputBorder(borderRadius: radiusControl),
      // The control border uses muted, never foam-line alone (web rule).
      enabledBorder: OutlineInputBorder(
        borderRadius: radiusControl,
        borderSide: BorderSide(color: Palette.muted),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: radiusControl,
        borderSide: BorderSide(color: Palette.deepCurrent, width: 2),
      ),
    ),
    navigationBarTheme: const NavigationBarThemeData(
      backgroundColor: Palette.surfaceWhite,
      indicatorColor: Palette.bgDeep,
      height: 68,
    ),
    dividerTheme: const DividerThemeData(color: Palette.foamLine, space: 1),
  );
}

/// Tabular figures keep readings aligned, like `.font-data` on the web.
const dataStyle = TextStyle(fontFeatures: [FontFeature.tabularFigures()]);
