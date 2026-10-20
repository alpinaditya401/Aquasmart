"""Ekspor data.

- GET /api/export?device_id=&kind=&period=&date=&format=json|csv (FR-028,
  dipakai tautan unduhan di halaman Laporan; port ExportRepository PHP):
  kind readings|alerts|commands|feeding_logs|reports|telemetry, jendela UTC
  hari/minggu/bulan, maksimal 10.000 baris. Header X-Export-Rows dan
  X-Provenance-Counts; meta.hardware_verified selalu false.
- GET /api/devices/<id>/export.csv?from=&to= (jalur lama, bacaan saja).
  Streaming via generator agar aman untuk data besar.
"""
import csv
import io
import json
import re
from datetime import datetime, timezone

from flask import Blueprint, g, Response, jsonify, request

from app import db, errors
from app.auth import login_required
from app.models import (ActuatorCommand, Alert, Device, DeviceTelemetry,
                        SensorReading, provenance_label)
from app.routes.reports import SOURCES, build_report, window
from app.routes.telemetry import _record

bp = Blueprint("export", __name__)

KINDS = ("readings", "alerts", "commands", "feeding_logs", "reports", "telemetry")
MAX_ROWS = 10000
_DEVICE_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
# Spreadsheet applications may run a cell that starts with a formula sign,
# even when it is quoted.
_FORMULA = re.compile(r"\s*[=+@-]")
_COMMAND_COLUMNS = ["id", "device_id", "created_at", "actuator", "value", "duration",
                    "status", "simulation", "completed_at", "provenance",
                    "source_session"]
CSV_COLUMNS = {
    "readings": ["id", "device_id", "created_at", "ph", "temperature", "turbidity",
                 "simulation", "provenance", "source_session"],
    "alerts": ["id", "device_id", "created_at", "severity", "message", "acknowledged",
               "acknowledged_at", "source", "provenance", "source_session"],
    "commands": _COMMAND_COLUMNS,
    "feeding_logs": _COMMAND_COLUMNS,
    "reports": ["day", "cnt", "ph_avg", "temperature_avg", "turbidity_avg",
                "simulation_samples", "non_simulation_samples"],
    "telemetry": ["created_at", "received_at", "provenance", "simulation",
                  "source_session", "temperature", "temperature_status",
                  "turbidity_adc", "turbidity_mv", "turbidity_sensor_mv",
                  "turbidity_mapping_percent", "soil_ph_adc", "soil_ph_mv", "tds_adc",
                  "tds_mv", "tds_ppm_estimate", "water_distance_cm", "tank_height_cm",
                  "water_level_percent", "ph_sensor", "calibrated"],
}


def _utc(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _epoch(dt):
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


def _reading_row(r):
    return {"id": r.id, "device_id": r.device_id, "created_at": r.created_at,
            "ph": r.ph, "temperature": r.temperature, "turbidity": r.turbidity,
            "simulation": bool(r.simulation), "provenance": r.provenance,
            "source_session": r.source_session}


def _alert_row(a):
    return {"id": a.id, "device_id": a.device_id, "created_at": a.created_at,
            "severity": a.severity, "message": a.message,
            "acknowledged": 1 if a.acknowledged else 0,
            "acknowledged_at": a.acknowledged_at, "provenance": a.provenance,
            "source_session": a.source_session,
            "source": provenance_label(a.provenance)}


def _command_row(c):
    return {"id": c.id, "device_id": c.device_id, "created_at": c.created_at,
            "actuator": c.actuator, "value": 1 if c.value else 0,
            "duration": c.duration, "status": c.status,
            "simulation": bool(c.simulation), "completed_at": c.completed_at,
            "provenance": c.provenance, "source_session": c.source_session}


def _query(kind, device_id, start, end):
    if kind == "readings":
        col = SensorReading.created_at
        return (SensorReading.query.filter(
            SensorReading.device_id == device_id, col >= _utc(start), col < _utc(end))
            .order_by(col, SensorReading.id), _reading_row)
    if kind == "alerts":
        col = Alert.created_at
        return (Alert.query.filter(
            Alert.device_id == device_id, col >= _utc(start), col < _utc(end))
            .order_by(col, Alert.id), _alert_row)
    if kind == "telemetry":
        col = DeviceTelemetry.created_at
        return (DeviceTelemetry.query.filter(
            DeviceTelemetry.device_id == device_id, col >= _utc(start), col < _utc(end))
            .order_by(col, DeviceTelemetry.id), _record)
    col = ActuatorCommand.created_at
    q = ActuatorCommand.query.filter(
        ActuatorCommand.device_id == device_id, col >= _epoch(start), col < _epoch(end))
    if kind == "feeding_logs":
        q = q.filter(ActuatorCommand.actuator == "feeder",
                     ActuatorCommand.status.in_(ActuatorCommand.TERMINAL))
    return q.order_by(col, ActuatorCommand.id), _command_row


def _source_counts(rows):
    counts = dict.fromkeys(SOURCES, 0)
    for row in rows:
        source = row.get("provenance")
        counts[source if source in SOURCES else "legacy_unverified"] += 1
    return counts


def _csv_cell(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    text = str(value)
    return "'" + text if isinstance(value, str) and _FORMULA.match(text) else text


def _csv(kind, rows, counts):
    columns = CSV_COLUMNS[kind] + [f"source_{s}" for s in SOURCES]
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        # Report groups carry their own source_* counts; other rows repeat the
        # export-wide counts, as the PHP export does.
        writer.writerow([_csv_cell(row[c] if c in row else counts[c[len("source_"):]])
                         for c in columns])
    return buf.getvalue()


@bp.get("/api/export")
@login_required
def export():
    fmt = request.args.get("format", "json")
    if fmt not in ("json", "csv"):
        return errors.unprocessable("Format harus csv atau json.")
    device_id = request.args.get("device_id", "")
    kind = request.args.get("kind", "readings")
    period = request.args.get("period", "day")
    date_s = request.args.get("date", "")
    try:
        day = datetime.strptime(date_s, "%Y-%m-%d") if _DATE.fullmatch(date_s) else None
    except ValueError:
        day = None
    if (not _DEVICE_ID.fullmatch(device_id) or kind not in KINDS
            or period not in ("day", "week", "month") or day is None):
        return errors.unprocessable("Filter ekspor tidak valid. Pilih perangkat, "
                                    "jenis data, tanggal, dan periode.")
    if not Device.query.filter_by(id=device_id, user_id=g.user.id).first():
        return errors.not_found("Perangkat tidak ditemukan.")

    start, end = window(period, day)
    if kind == "reports":
        report = build_report(device_id, period, date_s, start, end)
        rows, counts = report["groups"], report["source_counts"]
    else:
        query, to_row = _query(kind, device_id, start, end)
        found = query.limit(MAX_ROWS + 1).all()
        if len(found) > MAX_ROWS:
            return errors.unprocessable(
                "Ekspor melebihi 10.000 baris. Pilih periode lebih pendek.")
        rows = [to_row(r) for r in found]
        counts = _source_counts(rows)

    headers = {"X-Export-Rows": str(len(rows)),
               "X-Provenance-Counts": json.dumps(counts, separators=(",", ":"))}
    if fmt == "json":
        meta = {"device_id": device_id, "kind": kind, "period": period,
                "date": date_s, "timezone": "UTC", "start_at": _utc(start),
                "end_at_exclusive": _utc(end), "hardware_verified": False,
                "source_counts": counts}
        resp = jsonify({"meta": meta, "rows": rows})
        resp.headers.update(headers)
        return resp
    return Response(_csv(kind, rows, counts), mimetype="text/csv", headers={
        **headers, "Cache-Control": "no-store, private",
        "Content-Disposition": 'attachment; filename="aquasmart-export.csv"'})

COLUMNS = ["time", "ph", "temperature", "turbidity", "simulation",
           "provenance", "source_session"]


def _owned_device(device_id):
    device = Device.query.filter_by(id=device_id).first()
    if not device:
        return None, errors.not_found("Device tidak ditemukan.")
    if device.user_id != g.user.id:
        return None, errors.forbidden("Device bukan milik Anda.")
    return device, None


@bp.get("/api/devices/<device_id>/export.csv")
@login_required
def export_csv(device_id):
    device, err = _owned_device(device_id)
    if err:
        return err
    from_s = request.args.get("from", "")
    to_s = request.args.get("to", "")
    try:
        datetime.strptime(from_s, "%Y-%m-%d")
        datetime.strptime(to_s, "%Y-%m-%d")
    except ValueError:
        return errors.unprocessable("from & to harus format YYYY-MM-DD.")
    if from_s > to_s:
        return errors.unprocessable("from tidak boleh lebih besar dari to.")

    def generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(COLUMNS)
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)
        q = (SensorReading.query
             .filter(SensorReading.device_id == device.id,
                     SensorReading.created_at >= from_s,
                     SensorReading.created_at < to_s + "T23:59:59Z")
             .order_by(SensorReading.created_at.asc())
             .yield_per(500))
        for r in q:
            # Netralkan formula CSV injection (SKPL V3-FR14).
            row = [r.created_at, r.ph, r.temperature, r.turbidity,
                   int(r.simulation), r.provenance, r.source_session or ""]
            safe = [(("'" + str(v)) if isinstance(v, str)
                     and v[:1] in ("=", "+", "-", "@") else v) for v in row]
            writer.writerow(safe)
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    filename = f"aquasmart-{device.id}-{from_s}-{to_s}.csv"
    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition":
                 f'attachment; filename="{filename}"'})
