"""Kontrol aktuator dari dashboard: POST /api/devices/<id>/control (FR-018).

Lengkapi lifecycle perintah aktuator:
  dashboard enqueue (FR-018) → firmware poll (FR-016) → firmware ack (FR-017)

Aturan (SRS FR-018):
- Session admin + CSRF; tanpa CSRF → 403 csrf_mismatch.
- actuator ∈ {aerator, feeder, auto}.
- "auto" adalah mode, bukan aktuasi: set kolom devices.auto_mode,
  TIDAK masuk antrian perintah.
- Body {simulation: true} DITOLAK (firmware menolak perintah simulasi).
- Idempotensi request_id: request_id yang sama dengan parameter sama
  → kembalikan perintah lama (200); parameter berbeda → 409.
- Aktuator sibuk (ada perintah non-terminal & belum kedaluwarsa untuk
  device+actuator yang sama) → 409.
"""
import secrets
import time

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from app import db, errors
from app.auth import csrf_required, login_required
from app.models import ActuatorCommand, Device

bp = Blueprint("control", __name__)

ACTUATORS = ("aerator", "feeder", "auto")
NON_TERMINAL = ("pending", "delivered")
EXPIRES_SECONDS = 300


def _params_equal(cmd, actuator, value, duration):
    return (cmd.actuator == actuator
            and bool(cmd.value) == value
            and cmd.duration == duration)


def enqueue_command(device, user, actuator, value, duration, request_id=None,
                    simulation=False):
    """Enqueue perintah aktuator. Return (payload_dict, status_code)
    atau (error_response, None) bila gagal.

    Dipakai FR-018 (control) dan feeding logs (FR-020).
    """
    if actuator not in ACTUATORS:
        return errors.unprocessable("actuator harus aerator|feeder|auto."), None
    if not isinstance(value, bool):
        return errors.unprocessable("value harus boolean."), None
    if simulation:
        return errors.unprocessable("Perintah simulasi ditolak firmware."), None

    if actuator == "auto":
        device.auto_mode = 1 if value else 0
        db.session.commit()
        return ({"ok": True, "device_id": device.id,
                 "auto": bool(device.auto_mode)}, 200)

    if actuator == "feeder":
        if (isinstance(duration, bool) or not isinstance(duration, int)
                or not 1 <= duration <= 10):
            return errors.unprocessable(
                "duration feeder harus bilangan 1-10."), None
    else:
        duration = 0

    request_id = request_id or secrets.token_hex(16)
    existing = ActuatorCommand.query.filter_by(
        device_id=device.id, request_id=request_id).first()
    if existing:
        if _params_equal(existing, actuator, value, duration):
            return {"command": existing.to_dict()}, 200
        return errors.conflict(
            "request_id sudah dipakai dengan parameter berbeda."), None

    now = int(time.time())
    busy = (ActuatorCommand.query
            .filter_by(device_id=device.id, actuator=actuator)
            .filter(ActuatorCommand.status.in_(NON_TERMINAL))
            .filter(ActuatorCommand.expires_at > now)
            .first())
    if busy:
        return errors.conflict(
            "Aktuator sibuk: ada perintah yang belum selesai."), None

    cmd = ActuatorCommand(
        id=secrets.token_hex(16), device_id=device.id, user_id=user.id,
        actuator=actuator, value=1 if value else 0, duration=duration,
        request_id=request_id, status="pending", simulation=0,
        created_at=now, expires_at=now + EXPIRES_SECONDS,
        provenance="dashboard")
    db.session.add(cmd)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return errors.conflict("request_id bentrok, coba lagi."), None
    return {"command": cmd.to_dict()}, 201


@bp.post("/api/devices/<device_id>/control")
@login_required
@csrf_required
def control(device_id):
    device = Device.query.filter_by(id=device_id, user_id=g.user.id).first()
    if not device:
        return errors.not_found("Device tidak ditemukan.")
    if g.user.role != "admin":
        return errors.forbidden("Hanya admin yang boleh mengontrol aktuator.")

    body = request.get_json(silent=True) or {}
    actuator = body.get("actuator")
    value = body.get("value")
    duration = body.get("duration", 1) if actuator == "feeder" else 0

    payload, code = enqueue_command(
        device, g.user, actuator, value, duration,
        request_id=body.get("request_id"),
        simulation=body.get("simulation") is True)
    if code is None:
        return payload  # error response
    return jsonify(payload), code
