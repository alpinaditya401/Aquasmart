"""Observasi pertumbuhan manual (FR-027).

- GET  /api/growth-observations          → 200 terbaru milik user (frontend, PHP)
- POST /api/growth-observations          → admin + CSRF, body memuat device_id
- DELETE /api/growth-observations/<id>   → admin + CSRF, {deleted: true}
- GET + POST /api/devices/<id>/observations (jalur lama per device)

POST: {observed_at YYYY-MM-DD ≤ hari ini (UTC), weight_g?, length_cm? (> 0),
notes? ≤2000} — minimal satu dari weight_g/length_cm/notes.
"""
import math
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from app import db, errors
from app.auth import csrf_required, login_required
from app.models import Device, GrowthObservation

bp = Blueprint("observations", __name__)


def _owned_device(device_id):
    device = Device.query.filter_by(id=device_id).first()
    if not device:
        return None, errors.not_found("Device tidak ditemukan.")
    if device.user_id != g.user.id:
        return None, errors.forbidden("Device bukan milik Anda.")
    return device, None


@bp.get("/api/devices/<device_id>/observations")
@login_required
def list_observations(device_id):
    device, err = _owned_device(device_id)
    if err:
        return err
    rows = (GrowthObservation.query.filter_by(device_id=device.id)
            .order_by(GrowthObservation.observed_at.desc()).all())
    return jsonify({"observations": [o.to_dict() for o in rows]}), 200


def _create(device, body):
    observed_at = body.get("observed_at", "")
    try:
        obs_date = datetime.strptime(observed_at, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return errors.unprocessable("observed_at harus format YYYY-MM-DD.")
    if obs_date > datetime.now(timezone.utc).date():
        return errors.unprocessable(
            "observed_at tidak boleh tanggal masa depan (UTC).")
    weight_g = body.get("weight_g")
    length_cm = body.get("length_cm")
    notes = body.get("notes") or ""
    if not isinstance(notes, str):
        return errors.unprocessable("notes harus teks.")
    notes = notes.strip()
    # The frontend Observation schema requires positive sizes, so a stored 0
    # would make the observation list unreadable.
    for label, v in (("weight_g", weight_g), ("length_cm", length_cm)):
        if v is not None and (
                isinstance(v, bool) or not isinstance(v, (int, float))
                or not math.isfinite(v) or v <= 0):
            return errors.unprocessable(f"{label} harus angka lebih dari 0.")
    if len(notes) > 2000:
        return errors.unprocessable("notes maksimal 2000 karakter.")
    if weight_g is None and length_cm is None and not notes:
        return errors.unprocessable(
            "Minimal satu dari weight_g, length_cm, atau notes.")
    ob = GrowthObservation(
        user_id=g.user.id, device_id=device.id,
        observed_at=observed_at, weight_g=weight_g, length_cm=length_cm,
        notes=notes,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        provenance="manual")
    db.session.add(ob)
    db.session.commit()
    return jsonify({"observation": ob.to_dict()}), 201


@bp.post("/api/devices/<device_id>/observations")
@login_required
@csrf_required
def create_observation(device_id):
    device, err = _owned_device(device_id)
    if err:
        return err
    return _create(device, request.get_json(silent=True) or {})


@bp.get("/api/growth-observations")
@login_required
def list_growth_observations():
    rows = (GrowthObservation.query.filter_by(user_id=g.user.id)
            .order_by(GrowthObservation.observed_at.desc(),
                      GrowthObservation.id.desc())
            .limit(200).all())
    return jsonify({"observations": [o.to_dict() for o in rows]}), 200


@bp.post("/api/growth-observations")
@login_required
@csrf_required
def create_growth_observation():
    if g.user.role != "admin":
        return errors.forbidden("Hanya admin yang boleh mencatat observasi.")
    body = request.get_json(silent=True) or {}
    device = Device.query.filter_by(id=body.get("device_id"),
                                    user_id=g.user.id).first()
    if not device:
        return errors.not_found("Perangkat tidak ditemukan.")
    return _create(device, body)


@bp.delete("/api/growth-observations/<int:observation_id>")
@login_required
@csrf_required
def delete_growth_observation(observation_id):
    if g.user.role != "admin":
        return errors.forbidden("Hanya admin yang boleh menghapus observasi.")
    ob = GrowthObservation.query.filter_by(id=observation_id,
                                           user_id=g.user.id).first()
    if not ob:
        return errors.not_found("Observasi tidak ditemukan.")
    db.session.delete(ob)
    db.session.commit()
    return jsonify({"deleted": True}), 200
