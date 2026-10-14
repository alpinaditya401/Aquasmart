"""Pytest — kontrak API AquaSmart Flask (firmware + dashboard)."""
import hashlib
import json
import time

import pytest

from app import create_app, db
from app.models import ActuatorCommand, Device, DeviceCredential, SensorReading, User

DEVICE_ID = "AQS-TEST-01"
RAW_KEY = "test-device-key-1234567890"


@pytest.fixture()
def client():
    app = create_app("testing")
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as c:
        with app.app_context():
            db.create_all()
            import bcrypt
            pw = bcrypt.hashpw(b"rahasia123", bcrypt.gensalt()).decode()
            db.session.add(User(username="admin@t", contact="admin@t",
                                name="Admin", password_hash=pw, role="admin"))
            db.session.add(Device(id=DEVICE_ID, user_id=1, name="Kolam Tes",
                                  location="Lab"))
            db.session.add(DeviceCredential(
                device_id=DEVICE_ID,
                key_hash=hashlib.sha256(RAW_KEY.encode()).hexdigest(),
                rotated_at="2026-10-10T00:00:00Z"))
            db.session.commit()
        yield c


def _telemetry_body(**kw):
    body = {
        "created_at": "2026-10-10T10:00:00Z",
        "simulation": False,
        "provenance": "device",
        "source_session": "ABCDEF12",
        "temperature": 27.5,
        "temperature_status": "ok",
        "turbidity_adc": 1200,
        "turbidity_mv": 1500,
        "turbidity_mapping_percent": 42.5,
        "soil_ph_adc": 900,
        "soil_ph_mv": 1100,
        "tds_adc": 800,
        "tds_mv": 1000,
        "water_distance_cm": 10.0,
        "tank_height_cm": 20.0,
        "water_level_reference_confirmed": True,
        "water_probes_immersed": True,
        "calibrated": False,
        "ph_sensor": "soil_placeholder",
    }
    body.update(kw)
    return body


def _post_tl(client, body, key=RAW_KEY):
    return client.post(f"/api/devices/{DEVICE_ID}/telemetry", json=body,
                       headers={"X-Device-Key": key})


# --- publik ---
def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json["status"] == "ok"


def test_rules(client):
    r = client.get("/api/rules")
    assert r.status_code == 200
    assert r.json["version"] == "threshold-rules-v2"
    assert r.json["rule"]["turbidity_max"] == 50.0
    assert r.json["checksum"].startswith("sha256:")
    assert r.headers.get("Access-Control-Allow-Origin") == "*"


# --- auth ---
def _login(client):
    r = client.post("/api/auth/login",
                    json={"username": "admin@t", "password": "rahasia123"})
    assert r.status_code == 200
    return r.json["csrf_token"]


def test_auth_flow(client):
    csrf = _login(client)
    assert csrf
    r = client.get("/api/auth/me")
    assert r.status_code == 200 and r.json["user"]["username"] == "admin@t"
    r = client.post("/api/auth/logout")
    assert r.status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_login_salah(client):
    r = client.post("/api/auth/login",
                    json={"username": "admin@t", "password": "salah"})
    assert r.status_code == 401
    assert "error" in r.json


# --- telemetri (kontrak firmware) ---
def test_telemetry_201(client):
    r = _post_tl(client, _telemetry_body())
    assert r.status_code == 201, r.json
    assert r.json["provenance"] == "device"
    assert r.json["simulation"] is False


def test_telemetry_401_key_salah(client):
    r = _post_tl(client, _telemetry_body(), key="salah")
    assert r.status_code == 401


def test_telemetry_422_calibrated(client):
    r = _post_tl(client, _telemetry_body(calibrated=True))
    assert r.status_code == 422


def test_telemetry_422_provenance_mismatch(client):
    r = _post_tl(client, _telemetry_body(simulation=True, provenance="device"))
    assert r.status_code == 422


def test_telemetry_409_duplikat_beda_nilai(client):
    assert _post_tl(client, _telemetry_body()).status_code == 201
    body2 = _telemetry_body(temperature=99.9)
    r = _post_tl(client, body2)
    assert r.status_code == 409


def test_telemetry_idempoten_payload_sama(client):
    b = _telemetry_body()
    assert _post_tl(client, b).status_code == 201
    r = _post_tl(client, b)
    assert r.status_code == 201 and r.json.get("duplicate") is True


# --- commands (kontrak firmware) ---
def _seed_command(app):
    with app.app_context():
        now = int(time.time())
        cmd = ActuatorCommand(
            id="a" * 32, device_id=DEVICE_ID, user_id=1, actuator="aerator",
            value=1, duration=0, request_id="req-1", status="pending",
            simulation=0, created_at=now, expires_at=now + 300,
            provenance="device", source_session="ABCDEF12")
        db.session.add(cmd)
        db.session.commit()


def test_poll_dan_ack(client):
    from wsgi import app as _  # noqa
    # pakai app context dari fixture via client.application
    _seed_command(client.application)
    r = client.get(f"/api/device/devices/{DEVICE_ID}/commands",
                   headers={"X-Device-Key": RAW_KEY})
    assert r.status_code == 200
    cmds = r.json["commands"]
    assert len(cmds) == 1 and cmds[0]["status"] == "delivered"
    # poll kedua: sudah delivered → tidak muncul lagi
    r2 = client.get(f"/api/device/devices/{DEVICE_ID}/commands",
                    headers={"X-Device-Key": RAW_KEY})
    assert r2.json["commands"] == []
    # ack sukses
    r3 = client.post(
        f"/api/device/devices/{DEVICE_ID}/commands/{'a'*32}/ack",
        json={"status": "succeeded"}, headers={"X-Device-Key": RAW_KEY})
    assert r3.status_code == 200 and r3.json["status"] == "succeeded"
    # ack ulang → 409 (sudah terminal)
    r4 = client.post(
        f"/api/device/devices/{DEVICE_ID}/commands/{'a'*32}/ack",
        json={"status": "succeeded"}, headers={"X-Device-Key": RAW_KEY})
    assert r4.status_code == 409


def test_ack_tanpa_delivered_409(client):
    _seed_command(client.application)  # masih pending, belum di-poll
    r = client.post(
        f"/api/device/devices/{DEVICE_ID}/commands/{'a'*32}/ack",
        json={"status": "succeeded"}, headers={"X-Device-Key": RAW_KEY})
    assert r.status_code == 409


# --- readings & reports (dashboard) ---
def test_readings_dan_reports(client):
    _login(client)
    with client.application.app_context():
        db.session.add(SensorReading(
            device_id=DEVICE_ID, ph=7.0, temperature=27.5, turbidity=42.5,
            simulation=0, created_at="2026-10-10T10:00:00Z",
            provenance="device", source_session="ABCDEF12"))
        db.session.commit()
    r = client.get(f"/api/devices/{DEVICE_ID}/readings?limit=10")
    assert r.status_code == 200
    assert r.json["readings"][0]["temperature"] == 27.5
    assert r.json["readings"][0]["simulation"] is False
    r2 = client.get(f"/api/reports?device_id={DEVICE_ID}&period=day&date=2026-10-10")
    assert r2.status_code == 200
    assert r2.json["total_samples"] == 1
    assert r2.json["groups"][0]["temperature_avg"] == 27.5


def test_devices_thresholds_alerts(client):
    _login(client)
    r = client.get("/api/devices")
    assert r.status_code == 200
    devs = r.json["devices"]
    assert len(devs) == 1 and devs[0]["id"] == DEVICE_ID
    assert devs[0]["online"] is False and devs[0]["auto"] is False
    r = client.get("/api/settings/thresholds")
    assert r.status_code == 200
    assert r.json["thresholds"]["turbidity_max"] == 50.0
    r = client.get("/api/alerts?limit=1")
    assert r.status_code == 200
    assert r.json["alerts"] == [] and r.json["unacknowledged_count"] == 0


def test_readings_tanpa_login_401(client):
    assert client.get(f"/api/devices/{DEVICE_ID}/readings").status_code == 401


# --- FR-018 control aktuator (dashboard) ---
def _post_control(client, body, device_id=DEVICE_ID, csrf_token=None):
    headers = {}
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token
    return client.post(f"/api/devices/{device_id}/control",
                       json=body, headers=headers)


def _login_viewer(client):
    import bcrypt
    with client.application.app_context():
        pw = bcrypt.hashpw(b"lihat12345", bcrypt.gensalt()).decode()
        viewer = User(username="viewer@t", contact="viewer@t",
                      name="Viewer", password_hash=pw, role="viewer")
        db.session.add(viewer)
        db.session.flush()
        db.session.add(Device(id="AQS-VIEW-01", user_id=viewer.id,
                              name="Kolam Viewer", location="Lab"))
        db.session.commit()
    r = client.post("/api/auth/login",
                    json={"username": "viewer@t", "password": "lihat12345"})
    assert r.status_code == 200
    return r.json["csrf_token"]


def _command_count(app, **kw):
    with app.app_context():
        return ActuatorCommand.query.filter_by(**kw).count()


def test_control_aerator_201_dan_masuk_poll(client):
    csrf = _login(client)
    r = _post_control(client, {"actuator": "aerator", "value": True,
                               "request_id": "req-aer-1"}, csrf_token=csrf)
    assert r.status_code == 201, r.json
    cmd = r.json["command"]
    assert cmd["actuator"] == "aerator" and cmd["value"] is True
    assert cmd["status"] == "pending" and cmd["request_id"] == "req-aer-1"
    # firmware bisa mem-poll perintah hasil enqueue dashboard
    rp = client.get(f"/api/device/devices/{DEVICE_ID}/commands",
                    headers={"X-Device-Key": RAW_KEY})
    assert rp.status_code == 200
    assert len(rp.json["commands"]) == 1
    assert rp.json["commands"][0]["status"] == "delivered"


def test_control_tanpa_login_401(client):
    r = _post_control(client, {"actuator": "aerator", "value": True})
    assert r.status_code == 401


def test_control_tanpa_csrf_403_csrf_mismatch(client):
    _login(client)  # session cookie ada, header CSRF tidak
    r = _post_control(client, {"actuator": "aerator", "value": True})
    assert r.status_code == 403
    assert r.json["error"]["code"] == "csrf_mismatch"


def test_control_viewer_403(client):
    csrf = _login_viewer(client)
    r = _post_control(client, {"actuator": "aerator", "value": True},
                      device_id="AQS-VIEW-01", csrf_token=csrf)
    assert r.status_code == 403


def test_control_device_tidak_dikenal_404(client):
    csrf = _login(client)
    r = _post_control(client, {"actuator": "aerator", "value": True},
                      device_id="AQS-NOPE", csrf_token=csrf)
    assert r.status_code == 404


def test_control_auto_tidak_masuk_antrian(client):
    csrf = _login(client)
    r = _post_control(client, {"actuator": "auto", "value": True},
                      csrf_token=csrf)
    assert r.status_code == 200, r.json
    assert r.json["auto"] is True
    assert _command_count(client.application, device_id=DEVICE_ID) == 0
    with client.application.app_context():
        d = db.session.get(Device, DEVICE_ID)
        assert bool(d.auto_mode) is True
    r2 = _post_control(client, {"actuator": "auto", "value": False},
                       csrf_token=csrf)
    assert r2.status_code == 200 and r2.json["auto"] is False


def test_control_simulation_ditolak_422(client):
    csrf = _login(client)
    r = _post_control(client, {"actuator": "aerator", "value": True,
                               "simulation": True}, csrf_token=csrf)
    assert r.status_code == 422


def test_control_validasi_422(client):
    csrf = _login(client)
    assert _post_control(client, {"actuator": "pompa", "value": True},
                         csrf_token=csrf).status_code == 422
    assert _post_control(client, {"actuator": "aerator", "value": "on"},
                         csrf_token=csrf).status_code == 422
    assert _post_control(client, {"actuator": "feeder", "value": True,
                                  "duration": 11},
                         csrf_token=csrf).status_code == 422
    assert _post_control(client, {"actuator": "feeder", "value": True,
                                  "duration": 0},
                         csrf_token=csrf).status_code == 422


def test_control_feeder_default_duration_1(client):
    csrf = _login(client)
    r = _post_control(client, {"actuator": "feeder", "value": True},
                      csrf_token=csrf)
    assert r.status_code == 201, r.json
    assert r.json["command"]["duration"] == 1


def test_control_idempoten_request_id_sama(client):
    csrf = _login(client)
    body = {"actuator": "aerator", "value": True, "request_id": "req-idem-1"}
    r1 = _post_control(client, body, csrf_token=csrf)
    assert r1.status_code == 201
    r2 = _post_control(client, body, csrf_token=csrf)
    assert r2.status_code == 200
    assert r2.json["command"]["id"] == r1.json["command"]["id"]
    assert _command_count(client.application, device_id=DEVICE_ID) == 1


def test_control_request_id_beda_param_409(client):
    csrf = _login(client)
    b = {"actuator": "aerator", "value": True, "request_id": "req-idem-2"}
    assert _post_control(client, b, csrf_token=csrf).status_code == 201
    b2 = dict(b, value=False)
    r = _post_control(client, b2, csrf_token=csrf)
    assert r.status_code == 409


def test_control_aktuator_sibuk_409_lalu_bisa_lagi_setelah_terminal(client):
    csrf = _login(client)
    b1 = {"actuator": "aerator", "value": True, "request_id": "req-busy-1"}
    assert _post_control(client, b1, csrf_token=csrf).status_code == 201
    b2 = {"actuator": "aerator", "value": False, "request_id": "req-busy-2"}
    assert _post_control(client, b2, csrf_token=csrf).status_code == 409
    # selesaikan perintah pertama lewat lifecycle firmware
    cmd_id = None
    with client.application.app_context():
        c = ActuatorCommand.query.filter_by(request_id="req-busy-1").first()
        cmd_id = c.id
    hdrs = {"X-Device-Key": RAW_KEY}
    client.get(f"/api/device/devices/{DEVICE_ID}/commands", headers=hdrs)
    rack = client.post(
        f"/api/device/devices/{DEVICE_ID}/commands/{cmd_id}/ack",
        json={"status": "succeeded"}, headers=hdrs)
    assert rack.status_code == 200
    # aktuator bebas lagi
    r3 = _post_control(client, b2, csrf_token=csrf)
    assert r3.status_code == 201, r3.json


def test_workspace_dan_audit_logs(client):
    _login(client)
    r = client.get("/api/workspace")
    assert r.status_code == 200
    data = r.json
    assert data["owner_id"] == 1
    assert data["members"] == [{"id": 1, "name": "Admin", "role": "admin"}]
    r = client.get("/api/audit-logs?limit=20")
    assert r.status_code == 200
    assert r.json == {"audit_logs": []}
