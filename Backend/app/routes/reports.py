"""Agregasi laporan: GET /api/reports (FR-021).

Query: ?device_id=&period=day|week|month&date=YYYY-MM-DD
Bucket harian UTC dari sensor_readings. Periode kosong → groups kosong
(tidak difabrikasi). Setiap grup dan total memuat hitungan per provenance
(source_counts / source_*) seperti skema Report frontend.
"""
from datetime import datetime, timedelta

from flask import Blueprint, g, jsonify, request

from app import errors
from app.auth import login_required
from app.models import Device, SensorReading

bp = Blueprint("reports", __name__)

SOURCES = ("simulation", "device", "manual", "seed", "legacy_unverified")


def _source(reading):
    return reading.provenance if reading.provenance in SOURCES else "legacy_unverified"


@bp.get("/api/reports")
@login_required
def reports():
    device_id = request.args.get("device_id", "")
    period = request.args.get("period", "day")
    date_s = request.args.get("date", "")
    if period not in ("day", "week", "month"):
        return errors.unprocessable("period harus day|week|month.")
    try:
        day = datetime.strptime(date_s, "%Y-%m-%d")
    except ValueError:
        return errors.unprocessable("date harus format YYYY-MM-DD.")
    device = Device.query.filter_by(id=device_id, user_id=g.user.id).first()
    if not device:
        return errors.not_found("Device tidak dikenal.")

    if period == "day":
        start, end = day, day + timedelta(days=1)
    elif period == "week":
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=7)
    else:
        start = day.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)

    rows = (SensorReading.query
            .filter(SensorReading.device_id == device_id,
                    SensorReading.created_at >= start.strftime("%Y-%m-%d"),
                    SensorReading.created_at < end.strftime("%Y-%m-%d"))
            .order_by(SensorReading.created_at.asc()).all())

    buckets = {}
    for r in rows:
        key = r.created_at[:10]
        b = buckets.setdefault(key, {"ph": [], "temperature": [],
                                     "turbidity": [], "sim": 0, "nonsim": 0,
                                     "sources": dict.fromkeys(SOURCES, 0)})
        b["ph"].append(r.ph)
        b["temperature"].append(r.temperature)
        b["turbidity"].append(r.turbidity)
        b["sources"][_source(r)] += 1
        if r.simulation:
            b["sim"] += 1
        else:
            b["nonsim"] += 1

    def avg(xs):
        return round(sum(xs) / len(xs), 2) if xs else None

    groups = [{
        "day": k,
        "cnt": len(v["ph"]),
        "ph_avg": avg(v["ph"]),
        "temperature_avg": avg(v["temperature"]),
        "turbidity_avg": avg(v["turbidity"]),
        "simulation_samples": v["sim"],
        "non_simulation_samples": v["nonsim"],
        **{f"source_{s}": n for s, n in v["sources"].items()},
    } for k, v in sorted(buckets.items())]

    source_counts = dict.fromkeys(SOURCES, 0)
    for r in rows:
        source_counts[_source(r)] += 1
    simulation_samples = sum(1 for r in rows if r.simulation)

    return jsonify({
        "device_id": device_id,
        "period": period,
        "date": date_s,
        "timezone": "UTC",
        "start_at": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_at_exclusive": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "groups": groups,
        "total_samples": len(rows),
        "source_counts": source_counts,
        "simulation_samples": simulation_samples,
        "non_simulation_samples": len(rows) - simulation_samples,
    }), 200
