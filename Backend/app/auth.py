"""Autentikasi dua lapis AquaSmart.

1. Device (firmware ESP32): header X-Device-Key, diverifikasi sebagai
   SHA-256 hex terhadap device_credentials.key_hash.
2. User (dashboard): session cookie + CSRF via header X-CSRF-Token
   untuk semua request mutasi.
"""
import hashlib
import hmac
import secrets
from functools import wraps

from flask import g, request, session

from app import db
from app import errors
from app.models import DeviceCredential, User


def verify_device_key(device_id, raw_key):
    """Return True jika X-Device-Key cocok untuk device_id."""
    if not raw_key:
        return False
    cred = db.session.get(DeviceCredential, device_id)
    if not cred:
        return False
    digest = hashlib.sha256(raw_key.encode()).hexdigest()
    return hmac.compare_digest(digest, cred.key_hash)


def device_required(fn):
    @wraps(fn)
    def wrapper(device_id, *args, **kwargs):
        key = request.headers.get("X-Device-Key", "")
        if not verify_device_key(device_id, key):
            return errors.unauthorized("Device key salah atau hilang.")
        g.device_id = device_id
        return fn(device_id, *args, **kwargs)

    return wrapper


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return db.session.get(User, uid)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return errors.unauthorized("Sesi berakhir, silakan login lagi.")
        g.user = user
        return fn(*args, **kwargs)

    return wrapper


def csrf_required(fn):
    """Wajib untuk mutasi user: header X-CSRF-Token == session['csrf_token'].

    Kode error mengikuti kontrak SRS (FR-018 AC1): csrf_mismatch, 403.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        expected = session.get("csrf_token")
        got = request.headers.get("X-CSRF-Token", "")
        if not expected or not hmac.compare_digest(expected, got):
            return errors.err("csrf_mismatch", "CSRF token tidak valid.", 403)
        return fn(*args, **kwargs)

    return wrapper


def new_csrf_token():
    # 48 hex chars (24 bytes) — cocok dengan kontrak frontend (/^[0-9a-f]{48}$/)
    # dan perilaku backend PHP lama.
    token = secrets.token_hex(24)
    session["csrf_token"] = token
    return token
