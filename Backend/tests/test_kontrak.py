"""Kontrak respons untuk frontend Next.js dan firmware ESP32.

Kunci dan tipe di sini mengikuti FrontEnd/lib/api/schemas.ts, yang ditulis dari
backend PHP lama. Frontend menolak respons yang kehilangan field wajib, jadi field
yang hilang di sini membuat halaman dashboard gagal dimuat. Body telemetri meniru
buildTelemetry() di firmware/esp32/aquasmart_esp32/aqs_network.h.
"""
import hashlib
import re

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
