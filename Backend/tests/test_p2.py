"""Pytest — FR P2: heartbeat, raw telemetry, feeding logs, rule versions,
observations, export CSV, telemetry source."""
import hashlib
import time

import pytest

from app import create_app, db
from app.migrate import ensure_columns
from app.models import (ActuatorCommand, Device, DeviceCredential,
                        DeviceTelemetry, SensorReading, User)

DEVICE_ID = "AQS-TEST-01"
RAW_KEY = "test-device-key-1234567890"


@pytest.fixture()
def client():
    app = create_app("testing")
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as c:
        with app.app_context():
            db.create_all()
            ensure_columns(db)
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
            db.session.add(SensorReading(
                device_id=DEVICE_ID, ph=7.0, temperature=27.5, turbidity=42.5,
                simulation=0, created_at="2026-10-11T08:00:00Z",
                provenance="device", source_session="ABCDEF12"))
            db.session.commit()
        yield c


def _login(client):
    r = client.post("/api/auth/login",
                    json={"username": "admin@t", "password": "rahasia123"})
    assert r.status_code == 200
    return r.json["csrf_token"]


def _csrf(client):
    return {"X-CSRF-Token": _login(client)}


def _dkey():
    return {"X-Device-Key": RAW_KEY}


def _tl_body(ts, **kw):
    b = {"created_at": ts, "simulation": False, "provenance": "device",
         "source_session": "ABCDEF12", "temperature": 27.5,
         "temperature_status": "ok", "calibrated": False,
         "ph_sensor": "soil_placeholder"}
    b.update(kw)
    return b


# --- FR-012 heartbeat ---
def test_heartbeat_204(client):
    r = client.post(f"/api/devices/{DEVICE_ID}/heartbeat", headers=_dkey())
    assert r.status_code == 204
    with client.application.app_context():
        d = db.session.get(Device, DEVICE_ID)
        assert d.last_seen and d.online == 1


def test_heartbeat_tanpa_key_401(client):
    assert client.post(f"/api/devices/{DEVICE_ID}/heartbeat").status_code == 401


# --- FR-014 raw telemetry cursor ---
def test_raw_telemetry_paginasi(client):
    for i in range(3):
        r = client.post(f"/api/devices/{DEVICE_ID}/telemetry",
                        json=_tl_body(f"2026-10-11T09:0{i}:00Z"),
                        headers=_dkey())
        assert r.status_code == 201
    r = client.get(f"/api/devices/{DEVICE_ID}/telemetry/raw?limit=2",
                   headers=_dkey())
    assert r.status_code == 200
    assert len(r.json["telemetry"]) == 2
    assert r.json["next_cursor"] == "2026-10-11T09:01:00Z"
    r = client.get(f"/api/devices/{DEVICE_ID}/telemetry/raw?limit=2"
                   f"&cursor={r.json['next_cursor']}", headers=_dkey())
    assert len(r.json["telemetry"]) == 1
    assert r.json["next_cursor"] is None


def test_raw_telemetry_limit_dibatasi_1000(client):
    r = client.get(f"/api/devices/{DEVICE_ID}/telemetry/raw?limit=5000",
                   headers=_dkey())
    assert r.status_code == 200  # tidak error, limit dijepit


# --- telemetry source ---
def test_telemetry_source_default_simulated(client):
    r = client.post(f"/api/devices/{DEVICE_ID}/telemetry",
                    json=_tl_body("2026-10-11T10:00:00Z"), headers=_dkey())
    assert r.status_code == 201
    assert r.json["source"] == "simulated"


def test_telemetry_source_hardware(client):
    r = client.post(f"/api/devices/{DEVICE_ID}/telemetry",
                    json=_tl_body("2026-10-11T10:01:00Z", source="hardware"),
                    headers=_dkey())
    assert r.status_code == 201 and r.json["source"] == "hardware"


def test_telemetry_source_invalid_422(client):
    r = client.post(f"/api/devices/{DEVICE_ID}/telemetry",
                    json=_tl_body("2026-10-11T10:02:00Z", source="alien"),
                    headers=_dkey())
    assert r.status_code == 422


# --- FR-020 feeding logs ---
def test_feeding_logs_create_dan_list(client):
    h = _csrf(client)
    r = client.post(f"/api/devices/{DEVICE_ID}/feeding-logs",
                    json={"duration": 5}, headers=h)
    assert r.status_code == 201, r.json
    assert r.json["feeding_log"]["actuator"] == "feeder"
    cmd_id = r.json["feeding_log"]["id"]
    # tandai terminal agar masuk daftar feeding logs
    with client.application.app_context():
        c = db.session.get(ActuatorCommand, cmd_id)
        c.status = "succeeded"
        c.completed_at = int(time.time())
        db.session.commit()
    r = client.get(f"/api/devices/{DEVICE_ID}/feeding-logs")
    assert r.status_code == 200
    assert len(r.json["feeding_logs"]) == 1


# --- FR-026 rule versions ---
def test_rule_versions_bertambah(client):
    h = _csrf(client)
    body = {"ph_min": 6.5, "ph_max": 8.5, "temperature_min": 25.0,
            "temperature_max": 30.0, "turbidity_max": 50.0}
    client.put("/api/settings/thresholds", json=body, headers=h)
    client.put("/api/settings/thresholds",
               json={**body, "turbidity_max": 60.0}, headers=h)
    r = client.get("/api/rule-versions")
    assert r.status_code == 200
    vers = r.json["versions"]
    assert [v["version"] for v in vers] == ["2", "1"]
    assert vers[0]["config"]["turbidity_max"] == 60.0


# --- FR-027 observations ---
def test_observations_create_dan_list(client):
    h = _csrf(client)
    r = client.post(f"/api/devices/{DEVICE_ID}/observations",
                    json={"observed_at": "2026-10-11", "weight_g": 120.5,
                          "notes": "Sehat"}, headers=h)
    assert r.status_code == 201, r.json
    assert r.json["observation"]["provenance"] == "manual"
    r = client.get(f"/api/devices/{DEVICE_ID}/observations")
    assert len(r.json["observations"]) == 1


def test_observations_tanggal_depan_422(client):
    r = client.post(f"/api/devices/{DEVICE_ID}/observations",
                    json={"observed_at": "2999-01-01", "notes": "x"},
                    headers=_csrf(client))
    assert r.status_code == 422


def test_observations_kosong_422(client):
    r = client.post(f"/api/devices/{DEVICE_ID}/observations",
                    json={"observed_at": "2026-10-11"},
                    headers=_csrf(client))
    assert r.status_code == 422


# --- FR-028 export CSV ---
def test_export_csv(client):
    _login(client)
    r = client.get(f"/api/devices/{DEVICE_ID}/export.csv"
                   "?from=2026-10-11&to=2026-10-11")
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("text/csv")
    assert "attachment" in r.headers["Content-Disposition"]
    assert ".csv" in r.headers["Content-Disposition"]
    body = r.data.decode()
    assert body.splitlines()[0] == \
        "time,ph,temperature,turbidity,simulation,provenance,source_session"
    assert "2026-10-11T08:00:00Z" in body


def test_export_csv_tanggal_invalid_422(client):
    _login(client)
    r = client.get(f"/api/devices/{DEVICE_ID}/export.csv?from=x&to=y")
    assert r.status_code == 422
