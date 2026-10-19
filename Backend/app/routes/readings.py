"""Bacaan sensor ternormalisasi.

- GET  /api/devices/<id>/readings  (FR-015): untuk grafik, hanya pemilik device.
- POST /api/devices/<id>/readings  (X-Device-Key): ingest bacaan pH, suhu,
  kekeruhan, lalu evaluasi threshold pemilik. Port dari
  DeviceRepository::ingestReading PHP.

Telemetri mentah (/telemetry) sengaja tidak diubah jadi bacaan: sensor pH
yang terpasang adalah placeholder tanah, jadi nilai pH air harus dikirim
eksplisit lewat endpoint ini.
"""
import math
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from app import db, errors
from app.auth import device_required, login_required
from app.models import Alert, Device, SensorReading, ThresholdSetting
from app.routes.public import THRESHOLD_RULES_V2
from app.routes.telemetry import _parse_created_at

bp = Blueprint("readings", __name__)

_FIELDS = ("ph", "temperature", "turbidity")


def _reading_dict(r):
    return {
        "time": r.created_at,
        "ph": r.ph,
        "temperature": r.temperature,
        "turbidity": r.turbidity,
        "simulation": bool(r.simulation),
        "provenance": r.provenance,
        "source_session": r.source_session,
    }


@bp.get("/api/devices/<device_id>/readings")
@login_required
def readings(device_id):
    device = Device.query.filter_by(id=device_id, user_id=g.user.id).first()
    if not device:
        return errors.not_found("Device tidak dikenal.")
    try:
        limit = max(1, min(100, int(request.args.get("limit", 50))))
    except ValueError:
        return errors.unprocessable("limit harus 1–100.")
    rows = (SensorReading.query
            .filter_by(device_id=device_id)
            .order_by(SensorReading.created_at.asc())
            .limit(limit).all())
    return jsonify({"readings": [_reading_dict(r) for r in rows]}), 200


def _validate(body):
    if not isinstance(body, dict):
        return None, "Body harus JSON object."
    vals = {}
    for f in _FIELDS:
        v = body.get(f)
        if (isinstance(v, bool) or not isinstance(v, (int, float))
                or not math.isfinite(v)):
            return None, "Nilai sensor harus berupa angka valid."
        vals[f] = float(v)
    if (not 0 <= vals["ph"] <= 14 or not -50 <= vals["temperature"] <= 100
            or vals["turbidity"] < 0):
        return None, "Rentang nilai sensor tidak valid."
    simulation = body.get("simulation", False)
    if not isinstance(simulation, bool):
        return None, "simulation harus boolean."
    vals["simulation"] = simulation
    if "created_at" in body:
        created = _parse_created_at(body["created_at"])
        if not created:
            return None, "created_at harus ISO-8601 dengan zona waktu."
    else:
        created = datetime.now(timezone.utc)
    vals["created_at"] = created.strftime("%Y-%m-%dT%H:%M:%SZ")
    return vals, None


def _out_of_range(value, lo, hi):
    return value < lo or value > hi


def _raise_alerts(device, vals, provenance, previous):
    ts = db.session.get(ThresholdSetting, device.user_id)
    t = ({f: getattr(ts, f) for f in THRESHOLD_RULES_V2} if ts
         else THRESHOLD_RULES_V2)
    rules = [
        ("ph", "pH", t["ph_min"], t["ph_max"],
         "Periksa kalibrasi sensor dan kondisi air sebelum koreksi pH."),
        ("temperature", "Suhu", t["temperature_min"], t["temperature_max"],
         "Periksa sirkulasi dan kondisi suhu kolam."),
        ("turbidity", "Kekeruhan", 0.0, t["turbidity_max"],
         "Periksa endapan, filter, dan sisa pakan."),
    ]
    source = ("simulasi" if vals["simulation"]
              else "telemetri; kalibrasi belum diverifikasi")
    for key, label, lo, hi, advice in rules:
        value = vals[key]
        # Alert hanya saat nilai baru keluar ambang, supaya pelanggaran yang
        # berlanjut tidak membanjiri daftar alert.
        was_out = previous is not None and _out_of_range(
            getattr(previous, key), lo, hi)
        if _out_of_range(value, lo, hi) and not was_out:
            db.session.add(Alert(
                device_id=device.id, severity="warning",
                message=(f"{label} {value:g} di luar ambang {lo:g}-{hi:g}. "
                         f"{advice} Sumber: {source}; waktu {vals['created_at']}."),
                created_at=vals["created_at"], provenance=provenance))


@bp.post("/api/devices/<device_id>/readings")
@device_required
def ingest_reading(device_id):
    device = db.session.get(Device, device_id)
    if not device:
        return errors.not_found("Device tidak dikenal.")
    vals, err = _validate(request.get_json(silent=True))
    if err:
        return errors.unprocessable(err)
    provenance = "simulation" if vals["simulation"] else "device"

    existing = SensorReading.query.filter_by(
        device_id=device_id, created_at=vals["created_at"]).first()
    if existing:
        same = (all(getattr(existing, f) == vals[f] for f in _FIELDS)
                and bool(existing.simulation) == vals["simulation"])
        if not same:
            return errors.conflict("Timestamp sudah memiliki pembacaan berbeda.")
        return jsonify({"reading": _reading_dict(existing)}), 201

    previous = (SensorReading.query
                .filter_by(device_id=device_id, provenance=provenance)
                .order_by(SensorReading.created_at.desc()).first())
    reading = SensorReading(
        device_id=device_id, ph=vals["ph"], temperature=vals["temperature"],
        turbidity=vals["turbidity"], simulation=1 if vals["simulation"] else 0,
        created_at=vals["created_at"], provenance=provenance)
    db.session.add(reading)
    # Bacaan yang datang terlambat tetap disimpan, tetapi tidak menilai ulang
    # alert karena kondisi terkininya sudah dinilai bacaan yang lebih baru.
    if previous is None or vals["created_at"] > previous.created_at:
        _raise_alerts(device, vals, provenance, previous)
    device.online = 1
    device.last_seen = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    db.session.commit()
    return jsonify({"reading": _reading_dict(reading)}), 201
