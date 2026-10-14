"""Pytest — FR P1: profile, device mgmt, ack alert, schedules, thresholds."""
import hashlib

import pytest

from app import create_app, db
from app.migrate import ensure_columns
from app.models import (Alert, Device, DeviceCredential, DeviceInventory,
                        User)

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
            db.session.add(User(username="viewer@t", contact="viewer@t",
                                name="Viewer", password_hash=pw, role="viewer"))
            db.session.add(Device(id=DEVICE_ID, user_id=1, name="Kolam Tes",
                                  location="Lab"))
            db.session.add(DeviceCredential(
                device_id=DEVICE_ID,
                key_hash=hashlib.sha256(RAW_KEY.encode()).hexdigest(),
                rotated_at="2026-10-10T00:00:00Z"))
            db.session.add(DeviceInventory(
                serial_number="AQS-NEW-99", default_name="Kolam Baru",
                default_location="Gudang"))
            db.session.add(Alert(device_id=DEVICE_ID, severity="warning",
                                 message="Suhu tinggi",
                                 created_at="2026-10-11T08:00:00Z"))
            db.session.commit()
        yield c


def _login(client, username="admin@t"):
    r = client.post("/api/auth/login",
                    json={"username": username, "password": "rahasia123"})
    assert r.status_code == 200
    return r.json["csrf_token"]


def _csrf(client, username="admin@t"):
    return {"X-CSRF-Token": _login(client, username)}


# --- FR-005 profile ---
def test_profile_update_ok(client):
    r = client.patch("/api/profile", json={"name": "Alpin", "phone": "0812"},
                     headers=_csrf(client))
    assert r.status_code == 200
    assert r.json["user"]["name"] == "Alpin"


def test_profile_tanpa_csrf_403(client):
    _login(client)
    r = client.patch("/api/profile", json={"name": "X"})
    assert r.status_code == 403


def test_profile_nama_kosong_422(client):
    r = client.patch("/api/profile", json={"name": ""}, headers=_csrf(client))
    assert r.status_code == 422


# --- FR-009 claim ---
def test_claim_ok(client):
    r = client.post("/api/devices/claim", json={"serial_number": "aqs-new-99"},
                    headers=_csrf(client))
    assert r.status_code == 201, r.json
    assert r.json["device"]["id"] == "AQS-NEW-99"


def test_claim_duplikat_409(client):
    h = _csrf(client)
    assert client.post("/api/devices/claim",
                       json={"serial_number": "AQS-NEW-99"},
                       headers=h).status_code == 201
    r = client.post("/api/devices/claim", json={"serial_number": "AQS-NEW-99"},
                    headers=h)
    assert r.status_code == 409


def test_claim_serial_takdikenal_422(client):
    r = client.post("/api/devices/claim", json={"serial_number": "XXX-000"},
                    headers=_csrf(client))
    assert r.status_code == 422


# --- FR-010 rename ---
def test_rename_ok(client):
    r = client.patch(f"/api/devices/{DEVICE_ID}",
                     json={"name": "Kolam Lele", "location": "Belakang"},
                     headers=_csrf(client))
    assert r.status_code == 200 and r.json["updated"] is True


def test_rename_bukan_milik_403(client):
    r = client.patch(f"/api/devices/{DEVICE_ID}",
                     json={"name": "X", "location": "Y"},
                     headers=_csrf(client, "viewer@t"))
    assert r.status_code == 403


def test_rename_tidak_ada_404(client):
    r = client.patch("/api/devices/NOPE",
                     json={"name": "X", "location": "Y"},
                     headers=_csrf(client))
    assert r.status_code == 404


# --- FR-011 rotate key ---
def test_rotate_key_ok(client):
    h = _csrf(client)
    r = client.post(f"/api/devices/{DEVICE_ID}/key/rotate", headers=h)
    assert r.status_code == 200
    new_key = r.json["device_key"]
    assert new_key and new_key != RAW_KEY
    # key lama tidak berlaku lagi
    r2 = client.get(f"/api/device/devices/{DEVICE_ID}/commands",
                    headers={"X-Device-Key": RAW_KEY})
    assert r2.status_code == 401
    # key baru berlaku
    r3 = client.get(f"/api/device/devices/{DEVICE_ID}/commands",
                    headers={"X-Device-Key": new_key})
    assert r3.status_code == 200


def test_rotate_key_viewer_403(client):
    r = client.post(f"/api/devices/{DEVICE_ID}/key/rotate",
                    headers=_csrf(client, "viewer@t"))
    assert r.status_code == 403


# --- FR-023 ack alert ---
def test_ack_alert_ok(client):
    h = _csrf(client)
    r = client.post("/api/alerts/1/acknowledge", headers=h)
    assert r.status_code == 200, r.json
    assert r.json["alert"]["acknowledged"] is True
    assert r.json["alert"]["acknowledged_by"] == 1
    # ack ulang → 409
    r2 = client.post("/api/alerts/1/acknowledge", headers=h)
    assert r2.status_code == 409


def test_ack_alert_tidak_ada_404(client):
    r = client.post("/api/alerts/999/acknowledge", headers=_csrf(client))
    assert r.status_code == 404


# --- FR-024 schedules ---
def _sched_body(**kw):
    b = {"time": "06:30", "duration": 10, "days": "Setiap hari",
         "active": True}
    b.update(kw)
    return b


def test_schedules_crud(client):
    h = _csrf(client)
    r = client.post(f"/api/devices/{DEVICE_ID}/schedules",
                    json=_sched_body(), headers=h)
    assert r.status_code == 201, r.json
    sid = r.json["schedule"]["id"]
    assert r.json["schedule"]["end_time"] == "06:40"

    r = client.get(f"/api/devices/{DEVICE_ID}/schedules")
    assert r.status_code == 200 and len(r.json["schedules"]) == 1

    r = client.put(f"/api/schedules/{sid}", json=_sched_body(time="07:00"),
                   headers=h)
    assert r.status_code == 200
    assert r.json["schedule"]["time"] == "07:00"

    r = client.delete(f"/api/schedules/{sid}", headers=h)
    assert r.status_code == 200 and r.json["deleted"] is True


def test_schedule_time_invalid_422(client):
    r = client.post(f"/api/devices/{DEVICE_ID}/schedules",
                    json=_sched_body(time="25:99"), headers=_csrf(client))
    assert r.status_code == 422


def test_schedule_device_orang_lain_403(client):
    r = client.get(f"/api/devices/{DEVICE_ID}/schedules",
                   headers={"Cookie": ""})
    # tanpa login → 401; login sebagai viewer → 403
    assert r.status_code == 401
    _login(client, "viewer@t")
    r = client.get(f"/api/devices/{DEVICE_ID}/schedules")
    assert r.status_code == 403


# --- FR-025 PUT thresholds + rule version ---
def _thr_body(**kw):
    b = {"ph_min": 6.5, "ph_max": 8.5, "temperature_min": 25.0,
         "temperature_max": 30.0, "turbidity_max": 50.0}
    b.update(kw)
    return b


def test_put_thresholds_ok_dan_version(client):
    h = _csrf(client)
    r = client.put("/api/settings/thresholds", json=_thr_body(turbidity_max=60),
                   headers=h)
    assert r.status_code == 200, r.json
    assert r.json["thresholds"]["turbidity_max"] == 60.0
    assert r.json["rule_version"] == "1"
    r = client.put("/api/settings/thresholds", json=_thr_body(turbidity_max=70),
                   headers=h)
    assert r.json["rule_version"] == "2"


def test_put_thresholds_min_lebih_besar_422(client):
    r = client.put("/api/settings/thresholds",
                   json=_thr_body(ph_min=9.0, ph_max=8.0),
                   headers=_csrf(client))
    assert r.status_code == 422


def test_put_thresholds_negatif_422(client):
    r = client.put("/api/settings/thresholds",
                   json=_thr_body(turbidity_max=-1),
                   headers=_csrf(client))
    assert r.status_code == 422


def test_put_thresholds_viewer_403(client):
    r = client.put("/api/settings/thresholds", json=_thr_body(),
                   headers=_csrf(client, "viewer@t"))
    assert r.status_code == 403
