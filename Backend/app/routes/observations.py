"""Observasi pertumbuhan manual (FR-027): GET + POST /api/devices/<id>/observations.

POST (session + CSRF): {observed_at YYYY-MM-DD ≤ hari ini, weight_g?,
length_cm?, notes? ≤2000} — minimal satu dari weight_g/length_cm/notes.
"""
from datetime import date, datetime, timezone

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


@bp.post("/api/devices/<device_id>/observations")
@login_required
@csrf_required
def create_observation(device_id):
    device, err = _owned_device(device_id)
    if err:
        return err
    body = request.get_json(silent=True) or {}
    observed_at = body.get("observed_at", "")
    try:
        obs_date = datetime.strptime(observed_at, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return errors.unprocessable("observed_at harus format YYYY-MM-DD.")
    if obs_date > date.today():
        return errors.unprocessable(
            "observed_at tidak boleh tanggal masa depan.")
    weight_g = body.get("weight_g")
    length_cm = body.get("length_cm")
    notes = (body.get("notes") or "").strip()
    for label, v in (("weight_g", weight_g), ("length_cm", length_cm)):
        if v is not None and (
                isinstance(v, bool) or not isinstance(v, (int, float))
                or v < 0):
            return errors.unprocessable(f"{label} harus angka ≥ 0.")
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
