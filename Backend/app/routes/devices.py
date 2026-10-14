"""Daftar perangkat: GET /api/devices (FR-008).

Bentuk respons mengikuti skema frontend (DevicesResponse):
{ devices: [{id, name, location, online, aerator, feeder, auto,
             last_seen, latest_reading}] }
"""
from flask import Blueprint, g, jsonify

from app import db
from app.auth import login_required
from app.models import Device, SensorReading

bp = Blueprint("devices", __name__)


def _device_dict(d):
    latest = (SensorReading.query
              .filter_by(device_id=d.id)
              .order_by(SensorReading.created_at.desc())
              .first())
    return {
        "id": d.id,
        "name": d.name,
        "location": d.location,
        "online": bool(d.online),
        "aerator": bool(d.aerator),
        "feeder": bool(d.feeder),
        "auto": bool(d.auto_mode),
        "last_seen": d.last_seen,
        "latest_reading": {
            "ph": latest.ph,
            "temperature": latest.temperature,
            "turbidity": latest.turbidity,
            "simulation": bool(latest.simulation),
            "provenance": latest.provenance,
            "source_session": latest.source_session,
            "created_at": latest.created_at,
        } if latest else None,
    }


@bp.get("/api/devices")
@login_required
def list_devices():
    devices = (Device.query
               .filter_by(user_id=g.user.id)
               .order_by(Device.sort_order.asc(), Device.name.asc())
               .all())
    return jsonify({"devices": [_device_dict(d) for d in devices]}), 200
