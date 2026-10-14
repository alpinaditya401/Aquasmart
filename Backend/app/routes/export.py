"""Export CSV (FR-028): GET /api/devices/<id>/export.csv?from=&to=.

Streaming via generator agar aman untuk data besar.
Header: Content-Type: text/csv, Content-Disposition: attachment.
"""
import csv
import io
from datetime import datetime

from flask import Blueprint, g, Response, request

from app import db, errors
from app.auth import login_required
from app.models import Device, SensorReading

bp = Blueprint("export", __name__)

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
