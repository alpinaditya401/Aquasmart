"""Profil user: PATCH /api/profile (FR-005)."""
from flask import Blueprint, g, jsonify, request

from app import db, errors
from app.auth import csrf_required, login_required

bp = Blueprint("profile", __name__)


@bp.patch("/api/profile")
@login_required
@csrf_required
def update_profile():
    body = request.get_json(silent=True) or {}
    user = g.user
    if "name" in body:
        name = (body["name"] or "").strip()
        if not 1 <= len(name) <= 100:
            return errors.unprocessable("Nama wajib 1–100 karakter.")
        user.name = name
    if "phone" in body:
        phone = (body["phone"] or "").strip()
        if len(phone) > 20:
            return errors.unprocessable("Nomor HP maksimal 20 karakter.")
        user.phone = phone
    db.session.commit()
    return jsonify({"user": user.safe_dict()}), 200
