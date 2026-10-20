"""Threshold milik user: GET/PUT/PATCH /api/settings/thresholds (FR-025).

Bentuk respons mengikuti skema frontend (ThresholdsResponse):
{ thresholds: {ph_min, ph_max, temperature_min, temperature_max, turbidity_max} }

PUT atau PATCH (frontend memakai PATCH seperti PHP): session admin + CSRF.
Validasi: pH 0–14, min ≤ max untuk tiap pasangan, turbidity_max ≥ 0. Setiap
perubahan yang valid membuat rule_versions baru (version +1, tidak overwrite).

GET /api/rule-versions: id berupa SHA-256 dari user, versi, dan konfigurasi
(skema RuleVersion frontend), reading_count dari reading_rule_versions.
"""
import hashlib
import json
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func

from app import db, errors
from app.auth import csrf_required, login_required
from app.models import ReadingRuleVersion, RuleVersion, ThresholdSetting
from app.routes.public import THRESHOLD_RULES_V2

bp = Blueprint("settings", __name__)

FIELDS = ("ph_min", "ph_max", "temperature_min", "temperature_max",
          "turbidity_max")


def _thresholds_dict(ts):
    return {f: getattr(ts, f) for f in FIELDS}


@bp.get("/api/settings/thresholds")
@login_required
def get_thresholds():
    ts = db.session.get(ThresholdSetting, g.user.id)
    data = _thresholds_dict(ts) if ts else dict(THRESHOLD_RULES_V2)
    return jsonify({"thresholds": data}), 200


def _validate(body):
    vals = {}
    for f in FIELDS:
        v = body.get(f)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            return None, errors.unprocessable(f"{f} harus angka.")
        vals[f] = float(v)
    if not 0 <= vals["ph_min"] <= 14 or not 0 <= vals["ph_max"] <= 14:
        return None, errors.unprocessable("pH harus di antara 0 dan 14.")
    if vals["ph_min"] > vals["ph_max"]:
        return None, errors.unprocessable("ph_min tidak boleh > ph_max.")
    if vals["temperature_min"] > vals["temperature_max"]:
        return None, errors.unprocessable(
            "temperature_min tidak boleh > temperature_max.")
    if vals["turbidity_max"] < 0:
        return None, errors.unprocessable(
            "turbidity_max tidak boleh negatif.")
    return vals, None


@bp.route("/api/settings/thresholds", methods=["PUT", "PATCH"])
@login_required
@csrf_required
def put_thresholds():
    if g.user.role != "admin":
        return errors.forbidden("Hanya admin yang boleh mengubah threshold.")
    vals, err = _validate(request.get_json(silent=True) or {})
    if err:
        return err
    ts = db.session.get(ThresholdSetting, g.user.id)
    if not ts:
        ts = ThresholdSetting(user_id=g.user.id)
        db.session.add(ts)
    for f in FIELDS:
        setattr(ts, f, vals[f])

    # Snapshot rule version baru (version +1, tidak overwrite).
    last = (RuleVersion.query.filter_by(user_id=g.user.id)
            .order_by(RuleVersion.id.desc()).first())
    try:
        next_ver = str(int(last.version) + 1) if last else "1"
    except (ValueError, TypeError):
        next_ver = "1"
    rv = RuleVersion(
        user_id=g.user.id, version=next_ver,
        config_json=json.dumps(vals, sort_keys=True),
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    db.session.add(rv)
    db.session.commit()
    return jsonify({"thresholds": _thresholds_dict(ts),
                    "rule_version": next_ver}), 200


@bp.get("/api/rule-versions")
@login_required
def list_rule_versions():
    """Daftar versi rule milik user, terbaru dulu (FR-026)."""
    rows = (RuleVersion.query.filter_by(user_id=g.user.id)
            .order_by(RuleVersion.id.desc()).limit(50).all())
    counts = dict(db.session.query(ReadingRuleVersion.rule_id, func.count())
                  .filter(ReadingRuleVersion.rule_id.in_([r.id for r in rows]))
                  .group_by(ReadingRuleVersion.rule_id).all())
    return jsonify({
        "versions": [{
            "id": hashlib.sha256(
                f"{r.user_id}:{r.version}:{r.config_json}".encode()).hexdigest(),
            "version": r.version,
            "created_at": r.created_at,
            "reading_count": counts.get(r.id, 0),
            "config": json.loads(r.config_json),
        } for r in rows],
        "note": "Setiap perubahan threshold membuat versi baru; "
                "versi lama tidak dioverwrite.",
    }), 200
