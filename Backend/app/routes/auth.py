"""Autentikasi user dashboard: register/login/logout/me (FR-001..FR-004).

Hash password memakai bcrypt — kompatibel dengan hash PHP
password_hash() ($2y$) sehingga user lama tetap bisa login.
"""
import bcrypt
from flask import Blueprint, g, jsonify, request, session

from app import db, errors, limiter
from app.auth import csrf_required, current_user, login_required, new_csrf_token
from app.models import User

bp = Blueprint("auth", __name__)


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _check_password(plain: str, hashed: str) -> bool:
    h = hashed.encode()
    # bcrypt python memakai prefix $2b$; hash PHP memakai $2y$ (kompatibel).
    if h.startswith(b"$2y$"):
        h = b"$2b$" + h[4:]
    return bcrypt.checkpw(plain.encode(), h)


def _safe_user_payload(user):
    return {"user": user.safe_dict(), "csrf_token": session.get("csrf_token")}


@bp.post("/api/auth/register")
@limiter.limit("10 per minute")
def register():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    contact = (body.get("contact") or "").strip()
    password = body.get("password") or ""
    password_confirmation = body.get("password_confirmation") or ""

    if not (1 <= len(name) <= 100):
        return errors.unprocessable("Nama wajib 1–100 karakter.")
    if not contact:
        return errors.unprocessable("Kontak (email/no HP) wajib diisi.")
    if len(password) < 8:
        return errors.unprocessable("Password minimal 8 karakter.")
    if password != password_confirmation:
        return errors.unprocessable("Konfirmasi password tidak cocok.")
    if User.query.filter_by(username=contact).first():
        return errors.conflict("Kontak sudah terdaftar.")

    user = User(username=contact, contact=contact, name=name,
                password_hash=_hash_password(password), role="admin")
    db.session.add(user)
    db.session.commit()
    session["user_id"] = user.id
    new_csrf_token()
    return jsonify(_safe_user_payload(user)), 201


@bp.post("/api/auth/login")
@limiter.limit("30 per minute")
def login():
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    user = User.query.filter_by(username=username).first()
    if not user or not _check_password(password, user.password_hash):
        return errors.unauthorized("Kredensial salah.")
    session["user_id"] = user.id
    new_csrf_token()
    return jsonify(_safe_user_payload(user)), 200


@bp.post("/api/auth/logout")
@login_required
def logout():
    session.clear()
    return jsonify({"ok": True}), 200


@bp.get("/api/auth/me")
@login_required
def me():
    return jsonify({"user": g.user.safe_dict()}), 200
