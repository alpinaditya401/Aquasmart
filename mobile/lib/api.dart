import 'dart:convert';

import 'package:http/http.dart' as http;

/// Server address, set at build time:
///   flutter build apk --dart-define=AQUASMART_API_URL=https://server.example
/// The default reaches the host machine from the Android emulator, where the
/// backend runs through docker compose on port 8080.
const String defaultApiUrl = String.fromEnvironment(
  'AQUASMART_API_URL',
  defaultValue: 'http://10.0.2.2:8080',
);

class ApiException implements Exception {
  ApiException(this.status, this.code, this.message);

  final int status;
  final String code;
  final String message;

  @override
  String toString() => message;
}

class User {
  User({required this.name, required this.role});

  factory User.fromJson(Map<String, dynamic> j) =>
      User(name: j['name'] as String? ?? '', role: j['role'] as String? ?? '');

  final String name;
  final String role;

  bool get isAdmin => role == 'admin';
}

class Reading {
  Reading({
    required this.time,
    required this.ph,
    required this.temperature,
    required this.turbidity,
    required this.simulation,
    required this.provenance,
  });

  factory Reading.fromJson(Map<String, dynamic> j) => Reading(
    time: (j['time'] ?? j['created_at']) as String? ?? '',
    ph: (j['ph'] as num).toDouble(),
    temperature: (j['temperature'] as num).toDouble(),
    turbidity: (j['turbidity'] as num).toDouble(),
    simulation: j['simulation'] as bool? ?? false,
    provenance: j['provenance'] as String? ?? '',
  );

  final String time;
  final double ph;
  final double temperature;
  final double turbidity;
  final bool simulation;
  final String provenance;
}

class Device {
  Device({
    required this.id,
    required this.name,
    required this.location,
    required this.online,
    required this.aerator,
    required this.auto,
    required this.lastSeen,
    required this.latest,
  });

  factory Device.fromJson(Map<String, dynamic> j) => Device(
    id: j['id'] as String,
    name: j['name'] as String? ?? '',
    location: j['location'] as String? ?? '',
    online: j['online'] as bool? ?? false,
    aerator: j['aerator'] as bool? ?? false,
    auto: j['auto'] as bool? ?? false,
    lastSeen: j['last_seen'] as String?,
    latest: j['latest_reading'] == null
        ? null
        : Reading.fromJson(j['latest_reading'] as Map<String, dynamic>),
  );

  final String id;
  final String name;
  final String location;
  final bool online;
  final bool aerator;
  final bool auto;
  final String? lastSeen;
  final Reading? latest;
}

class Thresholds {
  Thresholds({
    required this.phMin,
    required this.phMax,
    required this.temperatureMin,
    required this.temperatureMax,
    required this.turbidityMax,
  });

  factory Thresholds.fromJson(Map<String, dynamic> j) => Thresholds(
    phMin: (j['ph_min'] as num).toDouble(),
    phMax: (j['ph_max'] as num).toDouble(),
    temperatureMin: (j['temperature_min'] as num).toDouble(),
    temperatureMax: (j['temperature_max'] as num).toDouble(),
    turbidityMax: (j['turbidity_max'] as num).toDouble(),
  );

  final double phMin;
  final double phMax;
  final double temperatureMin;
  final double temperatureMax;
  final double turbidityMax;
}

class Alert {
  Alert({
    required this.id,
    required this.deviceId,
    required this.message,
    required this.source,
    required this.acknowledged,
    required this.createdAt,
  });

  factory Alert.fromJson(Map<String, dynamic> j) => Alert(
    id: j['id'] as int,
    deviceId: j['device_id'] as String? ?? '',
    message: j['message'] as String? ?? '',
    source: j['source'] as String? ?? '',
    acknowledged: j['acknowledged'] as bool? ?? false,
    createdAt: j['created_at'] as String? ?? '',
  );

  final int id;
  final String deviceId;
  final String message;
  final String source;
  final bool acknowledged;
  final String createdAt;
}

class Command {
  Command({
    required this.actuator,
    required this.value,
    required this.duration,
    required this.status,
    required this.createdAt,
  });

  factory Command.fromJson(Map<String, dynamic> j) => Command(
    actuator: j['actuator'] as String? ?? '',
    value: j['value'] as bool? ?? false,
    duration: j['duration'] as int? ?? 0,
    status: j['status'] as String? ?? '',
    createdAt: j['created_at'] as int? ?? 0,
  );

  final String actuator;
  final bool value;
  final int duration;
  final String status;

  /// Epoch seconds, as stored by the backend for commands.
  final int createdAt;
}

/// Talks to the AquaSmart Flask backend with the same session cookie and
/// CSRF header the web dashboard uses.
class ApiClient {
  ApiClient({String? baseUrl, http.Client? client})
    : baseUrl = (baseUrl ?? defaultApiUrl).replaceAll(RegExp(r'/+$'), ''),
      _http = client ?? http.Client();

  final String baseUrl;
  final http.Client _http;
  String? _cookie;
  String? _csrf;
  User? user;

  bool get loggedIn => _cookie != null;

  Map<String, String> _headers({bool mutate = false}) => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Cookie': ?_cookie,
    if (mutate && _csrf != null) 'X-CSRF-Token': _csrf!,
  };

  void _keepCookie(http.Response r) {
    final raw = r.headers['set-cookie'];
    if (raw == null) return;
    final m = RegExp(r'aquasmart_session=([^;]*)').firstMatch(raw);
    if (m == null) return;
    // Logout answers with an expired, empty cookie.
    _cookie = m.group(1)!.isEmpty ? null : 'aquasmart_session=${m.group(1)}';
  }

  Future<Map<String, dynamic>> _send(
    String method,
    String path, {
    Object? body,
    bool mutate = false,
  }) async {
    final req = http.Request(method, Uri.parse('$baseUrl$path'))
      ..headers.addAll(_headers(mutate: mutate));
    if (body != null) req.body = jsonEncode(body);
    final http.Response r;
    try {
      r = await http.Response.fromStream(
        await _http.send(req).timeout(const Duration(seconds: 15)),
      );
    } on Exception {
      throw ApiException(
        0,
        'network',
        'Server tidak bisa dihubungi di $baseUrl. Periksa koneksi dan alamat server.',
      );
    }
    _keepCookie(r);
    final Map<String, dynamic> data = r.body.isEmpty
        ? <String, dynamic>{}
        : (jsonDecode(r.body) as Map<String, dynamic>? ?? {});
    if (r.statusCode >= 400) {
      final err = data['error'] as Map<String, dynamic>? ?? {};
      if (r.statusCode == 401) {
        _cookie = null;
        _csrf = null;
      }
      throw ApiException(
        r.statusCode,
        err['code'] as String? ?? 'error',
        err['message'] as String? ?? 'Permintaan gagal (HTTP ${r.statusCode}).',
      );
    }
    return data;
  }

  Future<User> login(String username, String password) async {
    final d = await _send(
      'POST',
      '/api/auth/login',
      body: {'username': username, 'password': password},
    );
    _csrf = d['csrf_token'] as String?;
    user = User.fromJson(d['user'] as Map<String, dynamic>);
    return user!;
  }

  Future<void> logout() async {
    try {
      await _send('POST', '/api/auth/logout', mutate: true);
    } finally {
      _cookie = null;
      _csrf = null;
      user = null;
    }
  }

  Future<List<Device>> devices() async {
    final d = await _send('GET', '/api/devices');
    return (d['devices'] as List)
        .map((e) => Device.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Reading>> readings(String deviceId, {int limit = 50}) async {
    final d = await _send(
      'GET',
      '/api/devices/${Uri.encodeComponent(deviceId)}/readings?limit=$limit',
    );
    return (d['readings'] as List)
        .map((e) => Reading.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Thresholds> thresholds() async {
    final d = await _send('GET', '/api/settings/thresholds');
    return Thresholds.fromJson(d['thresholds'] as Map<String, dynamic>);
  }

  Future<(List<Alert>, int)> alerts({int limit = 50}) async {
    final d = await _send('GET', '/api/alerts?limit=$limit');
    final list = (d['alerts'] as List)
        .map((e) => Alert.fromJson(e as Map<String, dynamic>))
        .toList();
    return (list, d['unacknowledged_count'] as int? ?? 0);
  }

  Future<void> acknowledge(int alertId) =>
      _send('PATCH', '/api/alerts/$alertId/acknowledge', mutate: true);

  Future<List<Command>> commands(String deviceId) async {
    final d = await _send(
      'GET',
      '/api/devices/${Uri.encodeComponent(deviceId)}/commands',
    );
    return (d['commands'] as List)
        .map((e) => Command.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Returns the updated device. A queued command is not proof that the
  /// actuator moved; the firmware's ack decides that.
  Future<Device> control(
    String deviceId,
    String actuator,
    bool value, {
    int? duration,
  }) async {
    final d = await _send(
      'POST',
      '/api/devices/${Uri.encodeComponent(deviceId)}/control',
      mutate: true,
      body: {'actuator': actuator, 'value': value, 'duration': ?duration},
    );
    return Device.fromJson(d['device'] as Map<String, dynamic>);
  }
}
