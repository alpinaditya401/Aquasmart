"""Konfigurasi AquaSmart Flask backend.

SECRET_KEY dan DATABASE_URL dibaca dari environment.
Untuk dev lokal, default memakai SQLite di instance/aquasmart.sqlite
(salinan skema demo.sqlite dari backend PHP — nol migrasi data).
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def normalize_db_url(url):
    # Railway gives postgres://, which SQLAlchemy rejects. The driver is named
    # explicitly because SQLAlchemy 2.1 maps a bare postgresql:// to psycopg 3,
    # while requirements.txt installs psycopg2.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-ganti-di-production")
    SQLALCHEMY_DATABASE_URI = normalize_db_url(os.environ.get("DATABASE_URL") or (
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "aquasmart.sqlite")))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # CSRF: token per-session, dikirim via header X-CSRF-Token
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Nama cookie session harus "aquasmart_session" — frontend (BFF/server
    # components) membaca cookie dengan nama ini, sesuai backend PHP lama.
    SESSION_COOKIE_NAME = "aquasmart_session"
    # Rate limit default; endpoint auth punya batas sendiri
    RATELIMIT_DEFAULT = "240 per minute"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False


config_by_name = {"default": Config, "testing": TestingConfig,
                  "production": Config}
