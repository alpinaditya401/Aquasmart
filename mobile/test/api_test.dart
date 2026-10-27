import 'dart:convert';

import 'package:aquasmart_mobile/api.dart';
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

const _user = {'name': 'Budi', 'role': 'admin'};

void main() {
  test(
    'login menyimpan cookie sesi dan CSRF untuk request berikutnya',
    () async {
      final seen = <http.Request>[];
      final api = ApiClient(
        baseUrl: 'http://srv/',
        client: MockClient((req) async {
          seen.add(req);
          if (req.url.path == '/api/auth/login') {
            return json(
              {'user': _user, 'csrf_token': 'abc'},
              200,
              headers: {'set-cookie': 'aquasmart_session=s1; HttpOnly; Path=/'},
            );
          }
          if (req.url.path == '/api/devices/K1/control') {
            return json({
              'device': {'id': 'K1', 'aerator': true},
              'command': {'id': 'c'},
            }, 201);
          }
          return json({'devices': []}, 200);
        }),
      );

      final u = await api.login('budi@contoh.id', 'rahasia');
      expect(u.isAdmin, isTrue);
      expect(api.loggedIn, isTrue);

      await api.devices();
      expect(seen[1].url.toString(), 'http://srv/api/devices');
      expect(seen[1].headers['Cookie'], 'aquasmart_session=s1');
      expect(seen[1].headers.containsKey('X-CSRF-Token'), isFalse);

      final d = await api.control('K1', 'aerator', true);
      expect(d.aerator, isTrue);
      expect(seen[2].headers['X-CSRF-Token'], 'abc');
      expect(jsonDecode(seen[2].body), {'actuator': 'aerator', 'value': true});
    },
  );

  test('error API memakai pesan dari server', () async {
    final api = ApiClient(
      baseUrl: 'http://srv',
      client: MockClient(
        (_) async => json({
          'error': {'code': 'conflict', 'message': 'Aktuator sibuk.'},
        }, 409),
      ),
    );
    await expectLater(
      api.control('K1', 'feeder', true, duration: 3),
      throwsA(
        isA<ApiException>()
            .having((e) => e.status, 'status', 409)
            .having((e) => e.message, 'message', 'Aktuator sibuk.'),
      ),
    );
  });

  test('401 menghapus sesi lokal', () async {
    var call = 0;
    final api = ApiClient(
      baseUrl: 'http://srv',
      client: MockClient(
        (_) async => ++call == 1
            ? json(
                {'user': _user, 'csrf_token': 'abc'},
                200,
                headers: {'set-cookie': 'aquasmart_session=s1; Path=/'},
              )
            : json({
                'error': {'code': 'unauthorized', 'message': 'Sesi berakhir.'},
              }, 401),
      ),
    );
    await api.login('a', 'b');
    await expectLater(api.devices(), throwsA(isA<ApiException>()));
    expect(api.loggedIn, isFalse);
  });

  test('server tidak terjangkau memberi pesan jaringan', () async {
    final api = ApiClient(
      baseUrl: 'http://srv',
      client: MockClient((_) async => throw const SocketLikeException()),
    );
    await expectLater(
      api.devices(),
      throwsA(isA<ApiException>().having((e) => e.code, 'code', 'network')),
    );
  });

  test('perangkat tanpa bacaan dan daftar alert terbaca', () async {
    final api = ApiClient(
      baseUrl: 'http://srv',
      client: MockClient(
        (req) async => req.url.path == '/api/alerts'
            ? json({
                'alerts': [
                  {
                    'id': 7,
                    'device_id': 'K1',
                    'message': 'pH 9.2 di luar ambang',
                    'source': 'SIMULASI',
                    'acknowledged': false,
                    'created_at': '2026-10-27T01:00:00Z',
                  },
                ],
                'unacknowledged_count': 4,
              }, 200)
            : json({
                'devices': [
                  {
                    'id': 'K1',
                    'name': 'Kolam A',
                    'location': 'L',
                    'online': false,
                    'aerator': false,
                    'feeder': false,
                    'auto': false,
                    'last_seen': null,
                    'latest_reading': null,
                  },
                ],
              }, 200),
      ),
    );
    final d = (await api.devices()).single;
    expect(d.latest, isNull);
    final (alerts, unread) = await api.alerts();
    expect(alerts.single.id, 7);
    expect(unread, 4);
  });
}

class SocketLikeException implements Exception {
  const SocketLikeException();
}
