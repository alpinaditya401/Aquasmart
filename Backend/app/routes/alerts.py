"""Alerts: GET /api/alerts, POST /api/alerts/<id>/acknowledge (FR-022, FR-023).

Bentuk respons mengikuti skema frontend (AlertsResponse / AlertAcknowledged):
{ alerts: [...], unacknowledged_count: n } dan { alert: {...} }.
"""
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from app import db, errors
from app.auth import csrf_required, login_required
from app.models import Alert, Device

bp = Blueprint("alerts", __name__)


@bp.get("/api/alerts")
@login_required
def list_alerts():
    try:
        limit = max(1, min(100, int(request.args.get("limit", 20))))
    except ValueError:
        return errors.unprocessable("limit harus 1–100.")
    own = (Alert.query.join(Device, Alert.device_id == Device.id)
           .filter(Device.user_id == g.user.id))
    rows = own.order_by(Alert.created_at.desc()).limit(limit).all()
    alerts = [{
        "id": a.id,
        "device_id": a.device_id,
        "severity": a.severity,
        "message": a.message,
        "acknowledged": bool(a.acknowledged),
        "created_at": a.created_at,
        "acknowledged_at": a.acknowledged_at,
        "provenance": a.provenance,
        "source_session": a.source_session,
    } for a in rows]
    unack = own.filter(Alert.acknowledged == 0).count()
    return jsonify({"alerts": alerts, "unacknowledged_count": unack}), 200


@bp.post("/api/alerts/<int:alert_id>/acknowledge")
@login_required
@csrf_required
def acknowledge(alert_id):
    alert = db.session.get(Alert, alert_id)
    if not alert:
        return errors.not_found("Alert tidak ditemukan.")
    device = Device.query.filter_by(id=alert.device_id,
                                    user_id=g.user.id).first()
    if not device:
        return errors.forbidden("Alert bukan milik perangkat Anda.")
    if alert.acknowledged:
        return errors.conflict("Alert sudah di-acknowledge sebelumnya.")
    alert.acknowledged = 1
    alert.acknowledged_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    alert.acknowledged_by = g.user.id
    db.session.commit()
    return jsonify({"alert": alert.to_dict()}), 200
