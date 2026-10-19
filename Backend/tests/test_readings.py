"""Pytest: kepemilikan data (alerts, readings, reports)."""
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
