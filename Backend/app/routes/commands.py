"""Commands firmware — kontrak yang TIDAK BOLEH berubah (FR-016, FR-017).

- GET  /api/device/devices/<id>/commands            (poll; X-Device-Key)
- POST /api/device/devices/<id>/commands/<cid>/ack  (X-Device-Key)

Prefix /api/device/devices/ adalah quirk nyata firmware ESP32 —
JANGAN disatukan dengan /api/devices/.

Lifecycle: pending → delivered → succeeded|failed|timeout.
Poll menandai pending→delivered. ACK hanya untuk command yang
sudah delivered dan belum terminal; selain itu 409.
"""
import time

from flask import Blueprint, jsonify, request

from app import db, errors
from app.auth import device_required
from app.models import ActuatorCommand, Device

bp = Blueprint("fw_commands", __name__)


@bp.get("/api/device/devices/<device_id>/commands")
@device_required
def poll(device_id):
    now = int(time.time())
    cmds = (ActuatorCommand.query
            .filter_by(device_id=device_id, status="pending")
            .filter(ActuatorCommand.expires_at > now)
            .order_by(ActuatorCommand.created_at.asc())
            .all())
    for c in cmds:
        c.status = "delivered"
        c.delivered_at = now
    db.session.commit()
    return jsonify({"commands": [c.to_dict() for c in cmds]}), 200


@bp.post("/api/device/devices/<device_id>/commands/<command_id>/ack")
@device_required
def ack(device_id, command_id):
    body = request.get_json(silent=True) or {}
    status = body.get("status")
    if status not in ActuatorCommand.TERMINAL:
        return errors.unprocessable("status harus succeeded|failed|timeout.")
    cmd = ActuatorCommand.query.filter_by(id=command_id,
                                          device_id=device_id).first()
    if not cmd:
        return errors.conflict("Command tidak ditemukan.")
    if cmd.status != "delivered":
        # Belum di-poll atau sudah terminal — firmware anggap terminal,
        # jangan aktuasi ulang.
        return errors.conflict("Command belum delivered atau sudah terminal.")
    cmd.status = status
    cmd.completed_at = int(time.time())
    # The dashboard toggle shows devices.aerator, so it changes only once the
    # firmware reports the relay was switched.
    if status == "succeeded" and cmd.actuator == "aerator":
        device = db.session.get(Device, device_id)
        if device:
            device.aerator = cmd.value
    db.session.commit()
    return jsonify({"ok": True, "id": cmd.id, "status": cmd.status}), 200
