"""Kontrak respons untuk frontend Next.js dan firmware ESP32.

Kunci dan tipe di sini mengikuti FrontEnd/lib/api/schemas.ts, yang ditulis dari
backend PHP lama. Frontend menolak respons yang kehilangan field wajib, jadi field
yang hilang di sini membuat halaman dashboard gagal dimuat. Body telemetri meniru
buildTelemetry() di firmware/esp32/aquasmart_esp32/aqs_network.h.
"""
import hashlib
import re
import time

import bcrypt
import pytest

from app import create_app, db
from app.models import Device, DeviceCredential, User

DEVICE = "AQS-KONTRAK-01"
KEY = "kunci-kontrak-1234567890"
UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
PROVENANCE = {"simulation", "device", "manual", "seed", "legacy_unverified"}


@pytest.fixture()
def client():
    app = create_app("testing")
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as c:
        with app.app_context():
            db.create_all()
            pw = bcrypt.hashpw(b"rahasia123", bcrypt.gensalt()).decode()
            db.session.add(User(username="a@t", contact="a@t", name="A",
                                password_hash=pw))
            db.session.flush()
            db.session.add_all([
                Device(id=DEVICE, user_id=1, name="Kolam Kontrak", location="Lab"),
                DeviceCredential(device_id=DEVICE,
                                 key_hash=hashlib.sha256(KEY.encode()).hexdigest(),
                                 rotated_at="2026-10-20T00:00:00Z"),
            ])
            db.session.commit()
        yield c


def _login(client):
    r = client.post("/api/auth/login",
                    json={"username": "a@t", "password": "rahasia123"})
    assert r.status_code == 200
    return {"X-CSRF-Token": r.json["csrf_token"]}


def _telemetry(**kw):
    body = {
        "device_id": DEVICE, "created_at": "2026-10-20T02:00:00Z",
        "provenance": "device", "simulation": False,
        "source_session": "esp32-a1b2c3d4-9f8e7d6c",
        "temperature": 27.25, "temperature_status": "ok",
        "turbidity_adc": 2000, "turbidity_mv": 1500,
        "soil_ph_adc": None, "soil_ph_mv": None,
        "tds_adc": 1500, "tds_mv": 1200,
        "turbidity_sensor_mv": 2500.0, "turbidity_mapping_percent": 50.0,
        "water_distance_cm": 18.0, "tank_height_cm": 50.0,
        "ph_sensor": "soil_placeholder", "calibrated": False,
    }
    body.update(kw)
    return body


def _post_telemetry(client, **kw):
    return client.post(f"/api/devices/{DEVICE}/telemetry", json=_telemetry(**kw),
                       headers={"X-Device-Key": KEY})


# --- firmware: telemetri ---
@pytest.mark.parametrize("session", ["esp32-a1b2c3d4-9f8e7d6c", "esp32-0-0",
                                     "seed_local_v1"])
def test_telemetri_terima_source_session_format_firmware(client, session):
    # Firmware membuang telemetri yang dijawab 422, jadi penolakan di sini
    # berarti data perangkat hilang tanpa jejak.
    assert _post_telemetry(client, source_session=session).status_code == 201


@pytest.mark.parametrize("session", ["esp32 a1b2", "pendek", "x" * 65,
                                     "esp32/a1b2c3", "esp32-a1b2c3\n"])
def test_telemetri_tolak_source_session_tidak_valid(client, session):
    assert _post_telemetry(client, source_session=session).status_code == 422


# --- frontend: alerts ---
ALERT_KEYS = {"id", "device_id", "severity", "message", "source", "provenance",
              "source_session", "acknowledged", "created_at", "acknowledged_at"}


def _post_reading(client, **kw):
    body = {"ph": 7.2, "temperature": 27.0, "turbidity": 10.0,
            "created_at": "2026-10-20T02:00:00Z"}
    body.update(kw)
    return client.post(f"/api/devices/{DEVICE}/readings", json=body,
                       headers={"X-Device-Key": KEY})


def _assert_alert(alert):
    assert ALERT_KEYS <= alert.keys(), ALERT_KEYS - alert.keys()
    assert alert["provenance"] in PROVENANCE
    assert isinstance(alert["source"], str) and alert["source"]
    assert UTC.match(alert["created_at"])


@pytest.mark.parametrize("simulation,label", [
    (False, "DEVICE / kalibrasi belum diverifikasi"), (True, "SIMULASI")])
def test_alerts_memuat_field_kontrak(client, simulation, label):
    assert _post_reading(client, ph=9.3, simulation=simulation).status_code == 201
    _login(client)
    r = client.get("/api/alerts?limit=1")
    assert r.status_code == 200
    _assert_alert(r.json["alerts"][0])
    assert r.json["alerts"][0]["source"] == label


def test_ack_alert_lewat_patch_seperti_frontend(client):
    _post_reading(client, ph=9.3)
    h = _login(client)
    alert_id = client.get("/api/alerts").json["alerts"][0]["id"]
    r = client.patch(f"/api/alerts/{alert_id}/acknowledge", headers=h)
    assert r.status_code == 200, r.json
    _assert_alert(r.json["alert"])
    assert r.json["alert"]["acknowledged"] is True
    assert client.get("/api/alerts").json["unacknowledged_count"] == 0


def test_ack_alert_patch_tanpa_csrf_403(client):
    _post_reading(client, ph=9.3)
    _login(client)
    alert_id = client.get("/api/alerts").json["alerts"][0]["id"]
    assert client.patch(f"/api/alerts/{alert_id}/acknowledge").status_code == 403


# --- frontend: telemetri di dashboard ---
TELEMETRY_KEYS = {
    "created_at", "received_at", "provenance", "simulation", "source_session",
    "temperature", "temperature_status", "turbidity_adc", "turbidity_mv",
    "turbidity_sensor_mv", "turbidity_mapping_percent", "soil_ph_adc", "soil_ph_mv",
    "tds_adc", "tds_mv", "tds_ppm_estimate", "water_distance_cm", "tank_height_cm",
    "water_level_percent", "water_level_reference_confirmed",
    "water_probes_immersed", "ph_sensor", "calibrated"}


def test_telemetri_get_untuk_dashboard(client):
    assert _post_telemetry(client).status_code == 201
    assert _post_telemetry(client, created_at="2026-10-20T02:01:00Z",
                           tds_mv=None, tds_adc=None, water_distance_cm=None,
                           tank_height_cm=None).status_code == 201
    _login(client)
    r = client.get(f"/api/devices/{DEVICE}/telemetry")
    assert r.status_code == 200, r.json
    assert isinstance(r.json["notice"], str) and r.json["notice"]
    newest, older = r.json["telemetry"]
    for rec in (newest, older):
        assert TELEMETRY_KEYS <= rec.keys(), TELEMETRY_KEYS - rec.keys()
        assert UTC.match(rec["created_at"]) and UTC.match(rec["received_at"])
        assert rec["ph_sensor"] == "soil_placeholder" and rec["calibrated"] is False
    assert newest["created_at"] == "2026-10-20T02:01:00Z"
    assert newest["tds_ppm_estimate"] is None and newest["water_level_percent"] is None
    # Same curve and rounding as the PHP backend (fixtures.json: 1200 mV -> 445.5).
    assert older["tds_ppm_estimate"] == 445.5
    assert older["water_level_percent"] == 64.0
    assert older["source_session"] == "esp32-a1b2c3d4-9f8e7d6c"


def test_telemetri_get_kosong_tetap_ada_notice(client):
    _login(client)
    r = client.get(f"/api/devices/{DEVICE}/telemetry")
    assert r.status_code == 200
    assert r.json["telemetry"] == [] and r.json["notice"]


def test_telemetri_get_butuh_login_dan_pemilik(client):
    assert client.get(f"/api/devices/{DEVICE}/telemetry").status_code == 401
    with client.application.app_context():
        pw = bcrypt.hashpw(b"rahasia123", bcrypt.gensalt()).decode()
        db.session.add(User(username="b@t", contact="b@t", name="B",
                            password_hash=pw))
        db.session.commit()
    client.post("/api/auth/login", json={"username": "b@t", "password": "rahasia123"})
    assert client.get(f"/api/devices/{DEVICE}/telemetry").status_code == 404


def test_telemetri_get_limit(client):
    for minute in range(3):
        _post_telemetry(client, created_at=f"2026-10-20T02:0{minute}:00Z")
    _login(client)
    r = client.get(f"/api/devices/{DEVICE}/telemetry?limit=2")
    assert [t["created_at"] for t in r.json["telemetry"]] == [
        "2026-10-20T02:02:00Z", "2026-10-20T02:01:00Z"]
    assert client.get(f"/api/devices/{DEVICE}/telemetry?limit=0").status_code == 422
    assert client.get(f"/api/devices/{DEVICE}/telemetry?limit=101").status_code == 422


# --- firmware dan frontend: command ---
COMMAND_KEYS = {"id", "device_id", "user_id", "actuator", "value", "duration",
                "request_id", "status", "simulation", "created_at", "expires_at",
                "delivered_at", "completed_at", "provenance", "source_session"}
COMMAND_STATUS = {"pending", "delivered", "succeeded", "failed", "timeout"}


def _assert_command(cmd):
    assert COMMAND_KEYS <= cmd.keys(), COMMAND_KEYS - cmd.keys()
    assert re.fullmatch(r"[0-9a-f]{32}", cmd["id"])
    assert cmd["provenance"] in PROVENANCE and cmd["status"] in COMMAND_STATUS
    assert isinstance(cmd["created_at"], int) and isinstance(cmd["expires_at"], int)


def test_poll_command_bisa_diterima_firmware(client):
    h = _login(client)
    r = client.post(f"/api/devices/{DEVICE}/control",
                    json={"actuator": "aerator", "value": True}, headers=h)
    assert r.status_code == 201, r.json
    poll = client.get(f"/api/device/devices/{DEVICE}/commands",
                      headers={"X-Device-Key": KEY})
    cmd = poll.json["commands"][0]
    # acceptCommand() in aqs_actuators.h drops a command unless simulation is
    # the boolean false, so without the field nothing is executed or ACKed.
    assert cmd["simulation"] is False
    assert isinstance(cmd["value"], bool) and isinstance(cmd["duration"], int)
    _assert_command(cmd)
    assert cmd["provenance"] == "manual" and cmd["user_id"] == 1
    assert isinstance(cmd["delivered_at"], int) and cmd["completed_at"] is None


def test_migrasi_provenance_dashboard_jadi_manual(client):
    from app.migrate import ensure_columns
    from app.models import ActuatorCommand
    with client.application.app_context():
        db.session.add(ActuatorCommand(
            id="a" * 32, device_id=DEVICE, user_id=1, actuator="aerator",
            value=1, duration=0, request_id="lama", status="succeeded",
            simulation=0, created_at=1, expires_at=2, provenance="dashboard"))
        db.session.commit()
        ensure_columns(db)
        assert db.session.get(ActuatorCommand, "a" * 32).provenance == "manual"


# --- frontend: halaman Kontrol ---
DEVICE_KEYS = {"id", "name", "location", "online", "aerator", "feeder", "auto",
               "last_seen", "latest_reading"}


def _control(client, h, **body):
    return client.post(f"/api/devices/{DEVICE}/control", json=body, headers=h)


def _poll_and_ack(client, status):
    cmd = client.get(f"/api/device/devices/{DEVICE}/commands",
                     headers={"X-Device-Key": KEY}).json["commands"][0]
    r = client.post(f"/api/device/devices/{DEVICE}/commands/{cmd['id']}/ack",
                    json={"status": status}, headers={"X-Device-Key": KEY})
    assert r.status_code == 200, r.json


def test_control_respons_device_dan_command(client):
    h = _login(client)
    r = _control(client, h, actuator="aerator", value=True)
    assert r.status_code == 201, r.json
    assert DEVICE_KEYS <= r.json["device"].keys() and r.json["device"]["id"] == DEVICE
    _assert_command(r.json["command"])
    r = _control(client, h, actuator="auto", value=True)
    assert r.status_code == 200, r.json
    assert r.json["command"] is None and r.json["device"]["auto"] is True


def test_daftar_command_per_device(client, monkeypatch):
    assert client.get(f"/api/devices/{DEVICE}/commands").status_code == 401
    h = _login(client)
    # Two commands in the same second would be ordered by their random ids.
    now = int(time.time())
    monkeypatch.setattr(time, "time", lambda: now)
    _control(client, h, actuator="aerator", value=True)
    monkeypatch.setattr(time, "time", lambda: now + 5)
    _control(client, h, actuator="feeder", value=True, duration=2)
    r = client.get(f"/api/devices/{DEVICE}/commands")
    assert r.status_code == 200, r.json
    assert [c["actuator"] for c in r.json["commands"]] == ["feeder", "aerator"]
    for cmd in r.json["commands"]:
        _assert_command(cmd)
    assert client.get("/api/devices/AQS-LAIN/commands").status_code == 404


def test_feeding_logs_berbentuk_command(client):
    h = _login(client)
    _control(client, h, actuator="feeder", value=True, duration=2)
    _poll_and_ack(client, "succeeded")
    logs = client.get(f"/api/devices/{DEVICE}/feeding-logs").json["feeding_logs"]
    assert len(logs) == 1
    _assert_command(logs[0])


@pytest.mark.parametrize("status,aerator", [("succeeded", True), ("failed", False)])
def test_status_aerator_ikut_ack_firmware(client, status, aerator):
    h = _login(client)
    _control(client, h, actuator="aerator", value=True)
    assert client.get("/api/devices").json["devices"][0]["aerator"] is False
    _poll_and_ack(client, status)
    assert client.get("/api/devices").json["devices"][0]["aerator"] is aerator
