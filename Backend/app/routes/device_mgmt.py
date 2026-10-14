"""Manajemen device: claim, rename, rotasi key (FR-009, FR-010, FR-011).

- POST /api/devices/claim — session + CSRF. Body {serial_number}
  (alias {serial} diterima). Serial dinormalisasi uppercase, harus ada di
  device_inventory dan belum diklaim. Unit produk butuh kode aktivasi
  (422, alur terpisah).
- PATCH /api/devices/<id> — session + CSRF. {name 1-100, location 1-150}.
  404 bila device tidak ada; 403 bila bukan milik user.
- POST /api/devices/<id>/key/rotate — session admin + CSRF. Key baru
  (token_urlsafe 32) ditampilkan SEKALI; yang disimpan hanya SHA-256.
"""
import hashlib
import re
import secrets
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from app import db, errors
from app.auth import csrf_required, login_required
from app.models import Device, DeviceCredential, DeviceInventory

bp = Blueprint("device_mgmt", __name__)

_SERIAL_RE = re.compile(r"^[A-Z0-9_-]{1,128}$")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _owned_device(device_id):
    device = Device.query.filter_by(id=device_id).first()
    if not device:
        return None, errors.not_found("Device tidak ditemukan.")
    if device.user_id != g.user.id:
        return None, errors.forbidden("Device bukan milik Anda.")
    return device, None


@bp.post("/api/devices/claim")
@login_required
@csrf_required
def claim():
    body = request.get_json(silent=True) or {}
    serial = (body.get("serial_number") or body.get("serial") or "")
    serial = serial.strip().upper()
    if not _SERIAL_RE.match(serial):
        return errors.unprocessable("Serial perangkat tidak valid.")

    inv = db.session.get(DeviceInventory, serial)
    if not inv:
        return errors.unprocessable("Serial perangkat belum terdaftar.")
    if inv.claimed_user_id is not None:
        return errors.conflict("Serial perangkat sudah diklaim.")

    device = Device(id=serial, user_id=g.user.id,
                    name=inv.default_name, location=inv.default_location)
    db.session.add(device)
    inv.claimed_user_id = g.user.id
    inv.claimed_at = _now()
    db.session.commit()
    return jsonify({"device": {"id": device.id, "name": device.name,
                               "location": device.location}}), 201


@bp.patch("/api/devices/<device_id>")
@login_required
@csrf_required
def rename(device_id):
    device, err = _owned_device(device_id)
    if err:
        return err
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    location = body.get("location")
    if (not isinstance(name, str) or not isinstance(location, str)
            or not name.strip() or not location.strip()
            or len(name.strip()) > 100 or len(location.strip()) > 150):
        return errors.unprocessable(
            "Nama wajib 1–100 karakter dan lokasi 1–150 karakter.")
    device.name = name.strip()
    device.location = location.strip()
    db.session.commit()
    return jsonify({"updated": True}), 200


@bp.post("/api/devices/<device_id>/key/rotate")
@login_required
@csrf_required
def rotate_key(device_id):
    device, err = _owned_device(device_id)
    if err:
        return err
    if g.user.role != "admin":
        return errors.forbidden("Hanya admin yang boleh merotasi device key.")
    raw_key = secrets.token_urlsafe(32)
    cred = db.session.get(DeviceCredential, device_id)
    if cred:
        cred.key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        cred.rotated_at = _now()
    else:
        cred = DeviceCredential(
            device_id=device_id,
            key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
            rotated_at=_now())
        db.session.add(cred)
    db.session.commit()
    # Key mentah hanya tampil SEKALI di respons ini.
    return jsonify({
        "device_id": device_id,
        "device_key": raw_key,
        "notice": "Simpan key ini sekarang. Key tidak akan ditampilkan lagi.",
    }), 200
