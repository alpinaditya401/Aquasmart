"""Feeding logs (FR-020): riwayat perintah feeder berstatus terminal.

- GET  /api/devices/<id>/feeding-logs → {feeding_logs: [...]} (bentuk Command)
- POST /api/devices/<id>/feeding-logs → enqueue perintah feeder
  (session admin + CSRF), body {duration 1-10, request_id?} → 201.

Feeding log = ActuatorCommand actuator='feeder' (tidak ada tabel terpisah
di skema baku). List hanya menampilkan yang terminal
(succeeded/failed/timeout).
"""
from flask import Blueprint, g, jsonify, request

from app import db, errors
from app.auth import csrf_required, login_required
from app.models import ActuatorCommand, Device
from app.routes.control import enqueue_command

bp = Blueprint("feeding", __name__)

TERMINAL = ActuatorCommand.TERMINAL


def _owned_device(device_id):
    device = Device.query.filter_by(id=device_id).first()
    if not device:
        return None, errors.not_found("Device tidak ditemukan.")
    if device.user_id != g.user.id:
        return None, errors.forbidden("Device bukan milik Anda.")
    return device, None


@bp.get("/api/devices/<device_id>/feeding-logs")
@login_required
def list_feeding_logs(device_id):
    device, err = _owned_device(device_id)
    if err:
        return err
    rows = (ActuatorCommand.query
            .filter_by(device_id=device.id, actuator="feeder")
            .filter(ActuatorCommand.status.in_(TERMINAL))
            .order_by(ActuatorCommand.created_at.desc())
            .limit(100).all())
    return jsonify({"feeding_logs": [c.to_dict() for c in rows]}), 200


@bp.post("/api/devices/<device_id>/feeding-logs")
@login_required
@csrf_required
def create_feeding_log(device_id):
    device, err = _owned_device(device_id)
    if err:
        return err
    if g.user.role != "admin":
        return errors.forbidden("Hanya admin yang boleh memberi pakan.")
    body = request.get_json(silent=True) or {}
    payload, code = enqueue_command(
        device, g.user, "feeder", True, body.get("duration", 5),
        request_id=body.get("request_id"))
    if code is None:
        return payload
    if code == 200:
        # Idempoten: request_id sama → kembalikan log lama.
        cmd = ActuatorCommand.query.filter_by(
            device_id=device.id,
            request_id=body.get("request_id")).first()
        return jsonify({"feeding_log": cmd.to_dict()}), 200
    cmd = ActuatorCommand.query.filter_by(
        id=payload["command"]["id"]).first()
    return jsonify({"feeding_log": cmd.to_dict()}), 201
