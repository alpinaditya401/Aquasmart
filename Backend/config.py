"""Konfigurasi AquaSmart Flask backend.

SECRET_KEY dan DATABASE_URL dibaca dari environment.
Untuk dev lokal, default memakai SQLite di instance/aquasmart.sqlite
(salinan skema demo.sqlite dari backend PHP — nol migrasi data).
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-ganti-di-production")
    _db_url = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "aquasmart.sqlite"),
    )
    # Railway memberi scheme postgres:// — SQLAlchemy butuh postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = "postgresql://" + _db_url[len("postgres://"):]
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # CSRF: token per-session, dikirim via header X-CSRF-Token
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Rate limit default; endpoint auth punya batas sendiri
    RATELIMIT_DEFAULT = "240 per minute"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False


config_by_name = {"default": Config, "testing": TestingConfig,
                  "production": Config}
