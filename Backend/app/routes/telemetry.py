"""Ingest telemetri ESP32: POST /api/devices/<id>/telemetry (FR-013).

Kontrak body (dari TelemetryRepository::ingest PHP, diverifikasi kode):
- created_at: UTC ketat (ISO-8601, akhiran Z)
- simulation: bool; provenance: 'simulation'|'device' (harus cocok)
- source_session: 8–64 karakter huruf, angka, _ atau - (firmware mengirim
  "esp32-<efuse>-<acak>")
- temperature + temperature_status (ok|disconnected|unverified)
- turbidity_adc/turbidity_mv (+turbidity_mapping_percent 0–100)
- soil_ph_adc/soil_ph_mv, tds_adc/tds_mv
- water_distance_cm + tank_height_cm (0–500, wajib berpasangan)
- calibrated: boolean (false = belum kalibrasi, true = sudah kalibrasi;
  direvisi 2026-10-14: menerima true agar data terkalibrasi bisa masuk;
  payload mentah tersimpan untuk audit); ph_sensor HARUS 'soil_placeholder'

Respons: 201 ternormalisasi; 409 timestamp duplikat beda nilai;
422 validasi; 401 key salah. Firmware menganggap 201/409/422 terminal.
"""
import json
import re
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from app import db, errors
from app.auth import device_required
from app.models import Device, DeviceTelemetry

bp = Blueprint("telemetry", __name__)

# Same pattern as the PHP backend; fullmatch because "$" in re.match would
# still accept a trailing newline.
_SESSION = re.compile(r"[A-Za-z0-9_-]{8,64}")
_TEMP_STATUS = ("ok", "disconnected", "unverified")


def _parse_created_at(value):
    if not isinstance(value, str):
        return None
    v = value.strip()
    try:
        if v.endswith("Z"):
            dt = datetime.fromisoformat(v[:-1] + "+00:00")
        else:
            dt = datetime.fromisoformat(v)
            if dt.tzinfo is None:
                return None
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _validate(body):
    """Return (cleaned_dict | None, error_message | None)."""
    if not isinstance(body, dict):
        return None, "Body harus JSON object."
    calibrated = body.get("calibrated")
    if not isinstance(calibrated, bool):
        return None, "calibrated harus boolean."
    if body.get("ph_sensor") != "soil_placeholder":
        return None, "ph_sensor harus 'soil_placeholder'."
    created = _parse_created_at(body.get("created_at"))
    if not created:
        return None, "created_at harus ISO-8601 UTC (mis. 2026-10-10T12:00:00Z)."
    simulation = body.get("simulation")
    if not isinstance(simulation, bool):
        return None, "simulation harus boolean."
    provenance = body.get("provenance")
    if provenance not in ("simulation", "device"):
        return None, "provenance harus 'simulation' atau 'device'."
    if (provenance == "simulation") != simulation:
        return None, "provenance harus cocok dengan simulation."
    source_session = body.get("source_session") or ""
    if not isinstance(source_session, str) or not _SESSION.fullmatch(source_session):
        return None, "source_session harus 8–64 karakter huruf, angka, _ atau -."
    tstat = body.get("temperature_status")
    if tstat not in _TEMP_STATUS:
        return None, "temperature_status harus ok|disconnected|unverified."
    temp = body.get("temperature")
    if tstat == "ok" and not isinstance(temp, (int, float)):
        return None, "temperature wajib angka bila status ok."
    mp = body.get("turbidity_mapping_percent")
    if mp is not None and not (isinstance(mp, (int, float)) and 0 <= mp <= 100):
        return None, "turbidity_mapping_percent harus 0–100."
    wd, th = body.get("water_distance_cm"), body.get("tank_height_cm")
    if (wd is None) != (th is None):
        return None, "water_distance_cm dan tank_height_cm wajib berpasangan."
    for k in ("water_distance_cm", "tank_height_cm"):
        v = body.get(k)
        if v is not None and not (isinstance(v, (int, float)) and 0 <= v <= 500):
            return None, f"{k} harus 0–500."
    source = body.get("source", "simulated")
    if source not in ("simulated", "hardware"):
        return None, "source harus 'simulated' atau 'hardware'."
    return {
        "created_at": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "simulation": simulation,
        "provenance": provenance,
        "source_session": source_session,
        "temperature": temp if isinstance(temp, (int, float)) else None,
        "turbidity_percent": mp,
        "source": source,
    }, None


@bp.post("/api/devices/<device_id>/telemetry")
@device_required
def ingest(device_id):
    device = db.session.get(Device, device_id)
    if not device:
        return errors.not_found("Device tidak dikenal.")
    body = request.get_json(silent=True)
    if body is None:
        return errors.unprocessable("Body JSON tidak valid.")
    if len(request.data or b"") > 64 * 1024:
        return errors.unprocessable("Body melebihi 64 KiB.")
    clean, err = _validate(body)
    if err:
        return errors.unprocessable(err)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = DeviceTelemetry(
        device_id=device_id,
        created_at=clean["created_at"],
        received_at=now,
        provenance=clean["provenance"],
        simulation=1 if clean["simulation"] else 0,
        source_session=clean["source_session"],
        payload=json.dumps(body, separators=(",", ":")),
        source=clean["source"],
    )
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Timestamp duplikat: cek apakah payload identik (idempoten) atau konflik.
        existing = DeviceTelemetry.query.filter_by(
            device_id=device_id, created_at=clean["created_at"]).first()
        if existing and existing.payload == row.payload:
            return jsonify({"ok": True, "duplicate": True,
                            "device_id": device_id,
                            "created_at": clean["created_at"]}), 201
        return errors.conflict("Timestamp sudah memiliki payload berbeda.")

    device.last_seen = now
    device.online = 1
    db.session.commit()
    return jsonify({
        "ok": True,
        "device_id": device_id,
        "created_at": clean["created_at"],
        "received_at": now,
        "simulation": clean["simulation"],
        "provenance": clean["provenance"],
        "source": clean["source"],
    }), 201


@bp.post("/api/devices/<device_id>/heartbeat")
@device_required
def heartbeat(device_id):
    """Heartbeat perangkat (FR-012): update last_seen, return 204."""
    device = db.session.get(Device, device_id)
    if not device:
        return errors.not_found("Device tidak dikenal.")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    device.last_seen = now
    device.online = 1
    db.session.commit()
    return "", 204


@bp.get("/api/devices/<device_id>/telemetry/raw")
@device_required
def raw_telemetry(device_id):
    """Telemetri mentah dengan paginasi cursor (FR-014).

    Query: ?cursor=<created_at terakhir>&limit=1..1000 (default 100).
    Respons: {telemetry: [...], next_cursor}.
    """
    device = db.session.get(Device, device_id)
    if not device:
        return errors.not_found("Device tidak dikenal.")
    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        return errors.unprocessable("limit harus angka.")
    limit = max(1, min(1000, limit))
    cursor = request.args.get("cursor", "")

    q = DeviceTelemetry.query.filter_by(device_id=device_id)
    if cursor:
        q = q.filter(DeviceTelemetry.created_at > cursor)
    rows = (q.order_by(DeviceTelemetry.created_at.asc())
            .limit(limit + 1).all())

    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].created_at if rows and has_more else None
    return jsonify({
        "telemetry": [{
            "created_at": r.created_at,
            "received_at": r.received_at,
            "provenance": r.provenance,
            "simulation": bool(r.simulation),
            "source": r.source or "simulated",
            "source_session": r.source_session,
            "payload": json.loads(r.payload),
        } for r in rows],
        "next_cursor": next_cursor,
    }), 200
