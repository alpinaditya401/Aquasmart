"""AquaSmart Flask backend — error envelope konsisten.

Semua error API memakai format:
    {"error": {"code": "<kode>", "message": "<pesan>"}}
sesuai kontrak backend PHP lama (firmware & frontend mengandalkannya).
"""
from flask import jsonify


def err(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


def bad_request(msg="Permintaan tidak valid."):
    return err("bad_request", msg, 400)


def unauthorized(msg="Butuh autentikasi."):
    return err("unauthorized", msg, 401)


def forbidden(msg="Akses ditolak."):
    return err("forbidden", msg, 403)


def not_found(msg="Tidak ditemukan."):
    return err("not_found", msg, 404)


def conflict(msg="Konflik data."):
    return err("conflict", msg, 409)


def unprocessable(msg="Validasi gagal."):
    return err("unprocessable", msg, 422)


def rate_limited(msg="Terlalu banyak permintaan, coba lagi nanti."):
    return err("rate_limited", msg, 429)
