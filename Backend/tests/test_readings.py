"""Pytest: kepemilikan data (alerts, readings, reports) dan ingest bacaan."""
import hashlib

import bcrypt
import pytest

from app import create_app, db
from app.models import Alert, Device, DeviceCredential, SensorReading, User

KEY_A = "kunci-device-a-1234567890"


@pytest.fixture()
def client():
    app = create_app("testing")
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as c:
        with app.app_context():
            db.create_all()
            pw = bcrypt.hashpw(b"rahasia123", bcrypt.gensalt()).decode()
            db.session.add_all([
                User(username="a@t", contact="a@t", name="A", password_hash=pw),
                User(username="b@t", contact="b@t", name="B", password_hash=pw),
            ])
            db.session.flush()
            db.session.add_all([
                Device(id="DEV-A", user_id=1, name="Kolam A", location="L"),
                Device(id="DEV-B", user_id=2, name="Kolam B", location="L"),
                DeviceCredential(device_id="DEV-A",
                                 key_hash=hashlib.sha256(KEY_A.encode()).hexdigest(),
                                 rotated_at="2026-10-19T00:00:00Z"),
                SensorReading(device_id="DEV-B", ph=7.0, temperature=27.0,
                              turbidity=5.0, simulation=0,
                              created_at="2026-10-19T01:00:00Z", provenance="device"),
                Alert(device_id="DEV-B", severity="warning", message="milik B",
                      created_at="2026-10-19T01:00:00Z"),
            ])
            db.session.commit()
        yield c


def _login(client, user):
    r = client.post("/api/auth/login", json={"username": user, "password": "rahasia123"})
    assert r.status_code == 200


def _post_reading(client, **kw):
    body = {"ph": 7.2, "temperature": 27.0, "turbidity": 10.0,
            "created_at": "2026-10-19T02:00:00Z"}
    body.update(kw)
    return client.post("/api/devices/DEV-A/readings", json=body,
                       headers={"X-Device-Key": KEY_A})


# --- kepemilikan ---
def test_alerts_hanya_milik_sendiri(client):
    _login(client, "a@t")
    r = client.get("/api/alerts")
    assert r.status_code == 200
    assert r.json["alerts"] == [] and r.json["unacknowledged_count"] == 0


def test_readings_device_orang_lain_404(client):
    _login(client, "a@t")
    assert client.get("/api/devices/DEV-B/readings").status_code == 404


def test_reports_device_orang_lain_404(client):
    _login(client, "a@t")
    r = client.get("/api/reports?device_id=DEV-B&period=day&date=2026-10-19")
    assert r.status_code == 404


def test_pemilik_tetap_bisa_lihat_datanya(client):
    _login(client, "b@t")
    assert len(client.get("/api/devices/DEV-B/readings").json["readings"]) == 1
    assert client.get("/api/alerts").json["unacknowledged_count"] == 1


# --- ingest bacaan ---
def test_ingest_tanpa_key_401(client):
    r = client.post("/api/devices/DEV-A/readings", json={"ph": 7, "temperature": 27, "turbidity": 1})
    assert r.status_code == 401


def test_ingest_tersimpan_dan_terbaca(client):
    r = _post_reading(client)
    assert r.status_code == 201
    assert r.json["reading"]["provenance"] == "device"
    _login(client, "a@t")
    rows = client.get("/api/devices/DEV-A/readings").json["readings"]
    assert [x["ph"] for x in rows] == [7.2]
    devs = client.get("/api/devices").json["devices"]
    assert devs[0]["online"] is True and devs[0]["latest_reading"]["ph"] == 7.2


@pytest.mark.parametrize("bad", [
    {"ph": "7"}, {"ph": True}, {"ph": 15}, {"temperature": 101},
    {"turbidity": -1}, {"simulation": "ya"}, {"created_at": "2026-10-19 02:00"},
])
def test_ingest_validasi_422(client, bad):
    assert _post_reading(client, **bad).status_code == 422


def test_ingest_duplikat(client):
    assert _post_reading(client).status_code == 201
    assert _post_reading(client).status_code == 201
    assert _post_reading(client, ph=6.9).status_code == 409


def test_alert_saat_keluar_ambang_sekali_saja(client):
    _post_reading(client, ph=7.0, created_at="2026-10-19T02:00:00Z")
    _post_reading(client, ph=9.2, created_at="2026-10-19T02:01:00Z")
    _post_reading(client, ph=9.4, created_at="2026-10-19T02:02:00Z")
    _login(client, "a@t")
    alerts = client.get("/api/alerts").json["alerts"]
    assert len(alerts) == 1 and alerts[0]["message"].startswith("pH 9.2")
    # kembali normal lalu keluar lagi: alert baru
    _post_reading(client, ph=7.1, created_at="2026-10-19T02:03:00Z")
    _post_reading(client, ph=9.0, created_at="2026-10-19T02:04:00Z")
    assert len(client.get("/api/alerts").json["alerts"]) == 2


def test_alert_pakai_threshold_pemilik(client):
    _login(client, "a@t")
    csrf = client.get("/api/auth/me").json["csrf_token"]
    t = {"ph_min": 6.5, "ph_max": 8.5, "temperature_min": 25,
         "temperature_max": 30, "turbidity_max": 5}
    assert client.put("/api/settings/thresholds", json=t,
                      headers={"X-CSRF-Token": csrf}).status_code == 200
    _post_reading(client, turbidity=10.0)
    msgs = [a["message"] for a in client.get("/api/alerts").json["alerts"]]
    assert len(msgs) == 1 and msgs[0].startswith("Kekeruhan 10")


def test_bacaan_terlambat_tidak_membuat_alert(client):
    _post_reading(client, ph=7.0, created_at="2026-10-19T03:00:00Z")
    _post_reading(client, ph=9.5, created_at="2026-10-19T02:00:00Z")
    _login(client, "a@t")
    assert client.get("/api/alerts").json["alerts"] == []
