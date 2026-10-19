"""Bacaan ternormalisasi untuk grafik: GET /api/devices/<id>/readings (FR-015)."""
from flask import Blueprint, g, jsonify, request

from app import db, errors
from app.auth import login_required
from app.models import Device, SensorReading

bp = Blueprint("readings", __name__)


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
    # Bentuk respons mengikuti skema frontend (ReadingsResponse):
    # { readings: [{time, ph, temperature, turbidity, simulation, provenance, source_session}] }
    return jsonify({"readings": [{
        "time": r.created_at,
        "ph": r.ph,
        "temperature": r.temperature,
        "turbidity": r.turbidity,
        "simulation": bool(r.simulation),
        "provenance": r.provenance,
        "source_session": r.source_session,
    } for r in rows]}), 200
