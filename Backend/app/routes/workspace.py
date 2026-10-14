"""Workspace dan audit log — implementasi minimal sesuai kontrak frontend.

Workspace adalah fitur Won't (out-of-scope): model single-user, di mana user
yang login adalah owner sekaligus satu-satunya member. Audit log belum
diimplementasikan di backend Flask; endpoint mengembalikan array kosong yang
valid sesuai kontrak (halaman menampilkan empty state, bukan error).
"""
from flask import Blueprint, g, jsonify, request

from app.auth import login_required

bp = Blueprint("workspace", __name__)


@bp.get("/api/workspace")
@login_required
def get_workspace():
    user = g.user
    return jsonify({
        "owner_id": user.id,
        "members": [{"id": user.id, "name": user.name, "role": user.role}],
    })


@bp.get("/api/audit-logs")
@login_required
def list_audit_logs():
    try:
        limit = max(1, min(100, int(request.args.get("limit", 20))))
    except (TypeError, ValueError):
        limit = 20
    return jsonify({"audit_logs": []})
