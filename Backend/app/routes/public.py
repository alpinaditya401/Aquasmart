"""Endpoint publik: health & threshold rules (FR-006, FR-007)."""
import hashlib
import json

from flask import Blueprint, jsonify

bp = Blueprint("public", __name__)

# Threshold aktif v2 — dari ThresholdRules PHP (diverifikasi kode).
THRESHOLD_RULES_V2 = {
    "ph_min": 6.5,
    "ph_max": 8.5,
    "temperature_min": 25.0,
    "temperature_max": 30.0,
    "turbidity_max": 50.0,
}
RULES_VERSION = "threshold-rules-v2"


def rules_checksum():
    canonical = json.dumps(THRESHOLD_RULES_V2, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


@bp.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "aquasmart-api"}), 200


@bp.get("/healthz")
def healthz():
    """Health check untuk orchestrator (Railway). Di luar /api/*."""
    return jsonify({"status": "ok"}), 200


@bp.get("/api/rules")
def rules():
    resp = jsonify(
        {
            "version": RULES_VERSION,
            "rule": THRESHOLD_RULES_V2,
            "checksum": rules_checksum(),
        }
    )
    # Satu-satunya endpoint dengan CORS terbuka (kontrak PHP lama).
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200
