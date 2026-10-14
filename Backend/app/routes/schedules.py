"""Feeding schedules CRUD (FR-024).

- GET  /api/devices/<id>/schedules → {schedules: [...]}
- POST /api/devices/<id>/schedules → {schedule: {...}} 201
- PUT  /api/schedules/<sid>          → {schedule: {...}}
- DELETE /api/schedules/<sid>        → {deleted: true}

Bentuk mengikuti skema frontend (Schedule): {id, time HH:MM, duration 1-30,
days enum, active, created_at}. Respons menyertakan end_time terhitung
(time + duration) untuk kejelasan jadwal.

Catatan: task meminta field start_time/end_time, tetapi skema DB baku
(feeding_schedules: time, duration, days, active) dan kontrak frontend
memakai time+duration — API mengikuti kontrak yang ada agar kompatibel.
"""
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, g, jsonify, request

from app import db, errors
from app.auth import csrf_required, login_required
from app.models import Device, FeedingSchedule

bp = Blueprint("schedules", __name__)

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
DAYS = ("Setiap hari", "Senin - Jumat", "Akhir pekan")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _end_time(time_str, duration):
    t = datetime.strptime(time_str, "%H:%M")
    return (t + timedelta(minutes=duration)).strftime("%H:%M")


def _schedule_dict(s):
    d = s.to_dict()
    d["end_time"] = _end_time(s.time, s.duration)
    return d


def _owned_device(device_id):
    device = Device.query.filter_by(id=device_id).first()
    if not device:
        return None, errors.not_found("Device tidak ditemukan.")
    if device.user_id != g.user.id:
        return None, errors.forbidden("Device bukan milik Anda.")
    return device, None


def _validate_body(body):
    """Return (clean | None, error_response | None)."""
    time_str = body.get("time")
    if not isinstance(time_str, str) or not _TIME_RE.match(time_str):
        return None, errors.unprocessable("time harus format HH:MM.")
    duration = body.get("duration", 10)
    if (isinstance(duration, bool) or not isinstance(duration, int)
            or not 1 <= duration <= 30):
        return None, errors.unprocessable("duration harus bilangan 1–30.")
    days = body.get("days", "Setiap hari")
    if days not in DAYS:
        return None, errors.unprocessable(
            "days harus salah satu: " + ", ".join(DAYS) + ".")
    active = body.get("active", True)
    if not isinstance(active, bool):
        return None, errors.unprocessable("active harus boolean.")
    return {"time": time_str, "duration": duration, "days": days,
            "active": active}, None


@bp.get("/api/devices/<device_id>/schedules")
@login_required
def list_schedules(device_id):
    device, err = _owned_device(device_id)
    if err:
        return err
    rows = (FeedingSchedule.query.filter_by(device_id=device.id)
            .order_by(FeedingSchedule.time.asc()).all())
    return jsonify({"schedules": [_schedule_dict(s) for s in rows]}), 200


@bp.post("/api/devices/<device_id>/schedules")
@login_required
@csrf_required
def create_schedule(device_id):
    device, err = _owned_device(device_id)
    if err:
        return err
    clean, err = _validate_body(request.get_json(silent=True) or {})
    if err:
        return err
    s = FeedingSchedule(device_id=device.id, time=clean["time"],
                        duration=clean["duration"], days=clean["days"],
                        active=1 if clean["active"] else 0,
                        created_at=_now(), updated_at=_now())
    db.session.add(s)
    db.session.commit()
    return jsonify({"schedule": _schedule_dict(s)}), 201


def _owned_schedule(sid):
    s = db.session.get(FeedingSchedule, sid)
    if not s:
        return None, errors.not_found("Jadwal tidak ditemukan.")
    device = Device.query.filter_by(id=s.device_id).first()
    if not device or device.user_id != g.user.id:
        return None, errors.forbidden("Jadwal bukan milik Anda.")
    return s, None


@bp.put("/api/schedules/<int:sid>")
@login_required
@csrf_required
def update_schedule(sid):
    s, err = _owned_schedule(sid)
    if err:
        return err
    clean, err = _validate_body(request.get_json(silent=True) or {})
    if err:
        return err
    s.time, s.duration, s.days = clean["time"], clean["duration"], clean["days"]
    s.active = 1 if clean["active"] else 0
    s.updated_at = _now()
    db.session.commit()
    return jsonify({"schedule": _schedule_dict(s)}), 200


@bp.delete("/api/schedules/<int:sid>")
@login_required
@csrf_required
def delete_schedule(sid):
    s, err = _owned_schedule(sid)
    if err:
        return err
    db.session.delete(s)
    db.session.commit()
    return jsonify({"deleted": True}), 200
