import 'dart:convert';

import 'package:aquasmart_mobile/api.dart';
import 'package:aquasmart_mobile/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

http.Response json(
  Object body,
  int status, {
  Map<String, String> headers = const {},
}) => http.Response(
  jsonEncode(body),
  status,
  headers: {'content-type': 'application/json', ...headers},
);

const _thresholds = {
  'thresholds': {
    'ph_min': 6.5,
    'ph_max': 8.5,
    'temperature_min': 25.0,
    'temperature_max': 30.0,
    'turbidity_max': 50.0,
  },
};

Map<String, Object?> _device(double ph) => {
  'id': 'K1',
  'name': 'Kolam Nila',
  'location': 'Belakang rumah',
  'online': true,
  'aerator': false,
  'feeder': false,
  'auto': false,
  'last_seen': '2026-10-27T01:00:00Z',
  'latest_reading': {
    'ph': ph,
    'temperature': 27.0,
    'turbidity': 10.0,
    'simulation': false,
    'provenance': 'device',
    'created_at': '2026-10-27T01:00:00Z',
  },
};

final controlBodies = <Map<String, dynamic>>[];

ApiClient _api({
  double ph = 7.1,
  bool loginOk = true,
  int unread = 0,
  List<Object> alerts = const [],
}) => ApiClient(
  baseUrl: 'http://srv',
  client: MockClient((req) async {
    switch (req.url.path) {
      case '/api/auth/login':
        return loginOk
            ? json(
                {
                  'user': {'name': 'Budi', 'role': 'admin'},
                  'csrf_token': 'x',
                },
                200,
                headers: {'set-cookie': 'aquasmart_session=s; Path=/'},
              )
            : json({
                'error': {
                  'code': 'unauthorized',
                  'message': 'Kredensial salah.',
                },
              }, 401);
      case '/api/devices':
        return json({
          'devices': [_device(ph)],
        }, 200);
      case '/api/settings/thresholds':
        return json(_thresholds, 200);
      case '/api/alerts':
        return json({'alerts': alerts, 'unacknowledged_count': unread}, 200);
      case '/api/devices/K1/readings':
        return json({
          'readings': [
            for (final v in [7.0, 7.2, ph])
              {
                'time': '2026-10-27T01:00:00Z',
                'ph': v,
                'temperature': 27.0,
                'turbidity': 10.0,
                'simulation': false,
                'provenance': 'device',
              },
          ],
        }, 200);
      case '/api/devices/K1/commands':
        return json({'commands': []}, 200);
      case '/api/devices/K1/control':
        controlBodies.add(jsonDecode(req.body) as Map<String, dynamic>);
        return json({
          'device': _device(ph),
          'command': {'id': 'c1'},
        }, 201);
    }
    return json({
      'error': {'code': 'not_found', 'message': 'x'},
    }, 404);
  }),
);

Future<void> _masuk(WidgetTester t) async {
  await t.enterText(find.byType(TextFormField).at(0), 'budi@contoh.id');
  await t.enterText(find.byType(TextFormField).at(1), 'rahasia123');
  await t.tap(find.widgetWithText(FilledButton, 'Masuk'));
  await t.pumpAndSettle();
}

void main() {
  testWidgets('form login menolak isian kosong', (t) async {
    await t.pumpWidget(AquaSmartApp(api: _api()));
    await t.tap(find.widgetWithText(FilledButton, 'Masuk'));
    await t.pump();
    expect(find.text('Isi email atau nomor HP.'), findsOneWidget);
    expect(find.text('Isi kata sandi.'), findsOneWidget);
  });

  testWidgets('kredensial salah tampil sebagai pesan, tetap di layar login', (
    t,
  ) async {
    await t.pumpWidget(AquaSmartApp(api: _api(loginOk: false)));
    await _masuk(t);
    expect(find.text('Email/nomor HP atau kata sandi salah.'), findsOneWidget);
    expect(find.text('Kolam Nila'), findsNothing);
  });

  testWidgets('setelah login, kolam aman tampil dengan bacaannya', (t) async {
    await t.pumpWidget(AquaSmartApp(api: _api()));
    await _masuk(t);
    expect(find.text('Kolam Nila'), findsOneWidget);
    expect(find.text('Semua parameter aman'), findsOneWidget);
    expect(find.text('7.1'), findsOneWidget);
  });

  testWidgets('tombol muat ulang mengambil data kolam lagi', (t) async {
    await t.pumpWidget(AquaSmartApp(api: _api()));
    await _masuk(t);
    await t.tap(find.byTooltip('Muat ulang'));
    await t.pumpAndSettle();
    expect(t.takeException(), isNull);
    expect(find.text('Kolam Nila'), findsOneWidget);
  });

  testWidgets('pH di luar batas disebut di kartu kolam', (t) async {
    await t.pumpWidget(AquaSmartApp(api: _api(ph: 9.2)));
    await _masuk(t);
    expect(find.text('pH di luar batas'), findsOneWidget);
  });

  testWidgets(
    'detail kolam: peringatan aktuasi, lalu perintah aerator terkirim',
    (t) async {
      controlBodies.clear();
      // Tall enough that the lazily built list holds the control section.
      t.view.physicalSize = const Size(800, 3200);
      t.view.devicePixelRatio = 1;
      addTearDown(t.view.reset);
      await t.pumpWidget(AquaSmartApp(api: _api()));
      await _masuk(t);
      await t.tap(find.text('Kolam Nila'));
      await t.pumpAndSettle();
      expect(find.text('Bacaan terakhir'), findsOneWidget);

      final tombol = find.widgetWithText(FilledButton, 'Nyalakan aerator');
      expect(find.text('Aktuasi fisik belum terbukti'), findsOneWidget);
      await t.tap(tombol);
      await t.pump();
      await t.pump(const Duration(milliseconds: 100));
      expect(controlBodies, [
        {'actuator': 'aerator', 'value': true},
      ]);
      expect(
        find.text(
          'Perintah masuk antrian. Status berubah setelah perangkat melapor.',
        ),
        findsOneWidget,
      );
      // Dispose the screen so its 10 s refresh timer does not outlive the test.
      await t.pumpWidget(const SizedBox());
    },
  );

  testWidgets('badge peringatan dan daftar alert', (t) async {
    await t.pumpWidget(
      AquaSmartApp(
        api: _api(
          unread: 1,
          alerts: [
            {
              'id': 1,
              'device_id': 'K1',
              'message': 'pH 9.2 di luar ambang 6.5-8.5.',
              'source': 'SIMULASI',
              'acknowledged': false,
              'created_at': '2026-10-27T01:00:00Z',
            },
          ],
        ),
      ),
    );
    await _masuk(t);
    expect(find.text('1'), findsOneWidget);
    await t.tap(find.text('Peringatan').last);
    await t.pumpAndSettle();
    expect(find.text('pH 9.2 di luar ambang 6.5-8.5.'), findsOneWidget);
    expect(find.text('Tandai sudah dibaca'), findsOneWidget);
  });
}
