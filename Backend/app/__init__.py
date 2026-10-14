"""AquaSmart Flask backend — application factory."""
import logging
import os

import click
from flask import Flask

from app import errors
from config import config_by_name

from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

log = logging.getLogger(__name__)

db = SQLAlchemy()


def build_limiter(redis_url=None):
    """Buat Limiter: Redis bila REDIS_URL ada, else in-memory + warning."""
    url = redis_url or os.environ.get("REDIS_URL")
    if url:
        return Limiter(key_func=get_remote_address, storage_uri=url)
    log.warning("REDIS_URL tidak di-set — rate limit memakai in-memory "
                "storage (tidak cocok untuk multi-worker).")
    return Limiter(key_func=get_remote_address, storage_uri="memory://")


limiter = build_limiter()


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    limiter.init_app(app)

    from app.routes import public, auth, telemetry, readings, commands, reports, devices, settings, alerts, control, profile, device_mgmt, schedules, feeding, observations, export
    app.register_blueprint(public.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(telemetry.bp)
    app.register_blueprint(readings.bp)
    app.register_blueprint(commands.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(devices.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(alerts.bp)
    app.register_blueprint(control.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(device_mgmt.bp)
    app.register_blueprint(schedules.bp)
    app.register_blueprint(feeding.bp)
    app.register_blueprint(observations.bp)
    app.register_blueprint(export.bp)

    @app.errorhandler(404)
    def _404(e):
        return errors.not_found("Endpoint tidak dikenal.")

    @app.errorhandler(405)
    def _405(e):
        return errors.err("method_not_allowed", "Method tidak diizinkan.", 405)

    @app.errorhandler(429)
    def _429(e):
        return errors.rate_limited()

    @app.errorhandler(500)
    def _500(e):
        return errors.err("internal_error", "Kesalahan server.", 500)

    # --- CORS manual untuk /api/* (tanpa dependency baru) ---
    # Origin diizinkan via env CORS_ORIGINS (comma-separated),
    # default http://localhost:3000. Preflight OPTIONS → 200.
    def _cors_origins():
        raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
        return [o.strip() for o in raw.split(",") if o.strip()]

    @app.before_request
    def _cors_preflight():
        from flask import request as _req
        if _req.method == "OPTIONS" and _req.path.startswith("/api/"):
            origin = _req.headers.get("Origin", "")
            if origin in _cors_origins():
                resp = app.make_response(("", 200))
                resp.headers["Access-Control-Allow-Origin"] = origin
                resp.headers["Access-Control-Allow-Methods"] = \
                    "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                resp.headers["Access-Control-Allow-Headers"] = \
                    "Content-Type, X-CSRF-Token, X-Device-Key"
                resp.headers["Access-Control-Allow-Credentials"] = "true"
                return resp
            return "", 200

    @app.after_request
    def _cors_headers(resp):
        from flask import request as _req
        if _req.path.startswith("/api/"):
            origin = _req.headers.get("Origin", "")
            if (origin in _cors_origins()
                    and "Access-Control-Allow-Origin" not in resp.headers):
                resp.headers["Access-Control-Allow-Origin"] = origin
                resp.headers["Access-Control-Allow-Credentials"] = "true"
        return resp

    @app.cli.command("expire-commands")
    def expire_commands_cli():
        """Ubah command pending yang kedaluwarsa menjadi 'expired'."""
        from app.scheduler import expire_pending_commands
        with app.app_context():
            n = expire_pending_commands()
        click.echo(f"expired={n}")

    # Scheduler hanya aktif bila eksplisit — mencegah dobel multi-worker.
    if os.environ.get("SCHEDULER_ENABLED", "false").lower() == "true":
        from app.scheduler import start_scheduler
        start_scheduler(app)

    return app
