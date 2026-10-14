"""Pytest — scheduler expire-commands & rate limit storage."""
import os
import time
from unittest import mock

import pytest

from app import build_limiter, create_app, db
from app.migrate import ensure_columns
from app.models import ActuatorCommand, Device, User


@pytest.fixture()
def app_():
    app = create_app("testing")
    app.config["SECRET_KEY"] = "test-secret"
    with app.app_context():
        db.create_all()
        ensure_columns(db)
        import bcrypt
        pw = bcrypt.hashpw(b"x", bcrypt.gensalt()).decode()
        db.session.add(User(username="u", name="U", password_hash=pw))
        db.session.add(Device(id="D1", user_id=1, name="N", location="L"))
        now = int(time.time())
        db.session.add(ActuatorCommand(
            id="o" * 32, device_id="D1", user_id=1, actuator="aerator",
            value=1, duration=0, request_id="r-old", status="pending",
            simulation=0, created_at=now - 3600, expires_at=now + 300))
        db.session.add(ActuatorCommand(
            id="n" * 32, device_id="D1", user_id=1, actuator="aerator",
            value=1, duration=0, request_id="r-new", status="pending",
            simulation=0, created_at=now, expires_at=now + 300))
        db.session.commit()
    return app


def test_expire_commands_cli(app_):
    runner = app_.test_cli_runner()
    with mock.patch.dict(os.environ, {"COMMAND_EXPIRY_MINUTES": "10"}):
        res = runner.invoke(args=["expire-commands"])
    assert res.exit_code == 0, res.output
    assert "expired=1" in res.output
    with app_.app_context():
        assert db.session.get(ActuatorCommand, "o" * 32).status == "expired"
        assert db.session.get(ActuatorCommand, "n" * 32).status == "pending"


def test_expire_tidak_menyentuh_delivered(app_):
    with app_.app_context():
        c = db.session.get(ActuatorCommand, "o" * 32)
        c.status = "delivered"
        db.session.commit()
    runner = app_.test_cli_runner()
    res = runner.invoke(args=["expire-commands"])
    assert "expired=0" in res.output


def test_scheduler_hanya_bila_enabled():
    with mock.patch.dict(os.environ, {"SCHEDULER_ENABLED": "true"}):
        app = create_app("testing")
        assert "scheduler" in app.extensions
        app.extensions["scheduler"].shutdown(wait=False)
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("SCHEDULER_ENABLED", None)
        app2 = create_app("testing")
        assert "scheduler" not in app2.extensions


def test_rate_limit_redis_bila_ada():
    lim = build_limiter("redis://localhost:6379/0")
    assert lim._storage_uri == "redis://localhost:6379/0"


def test_rate_limit_fallback_memory():
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("REDIS_URL", None)
        lim = build_limiter()
    assert lim._storage_uri == "memory://"


def test_healthz():
    from app import create_app
    app = create_app("testing")
    c = app.test_client()
    r = c.get("/healthz")
    assert r.status_code == 200 and r.json == {"status": "ok"}


def test_cors_preflight():
    import os
    from unittest import mock
    from app import create_app
    with mock.patch.dict(os.environ, {"CORS_ORIGINS": "https://x.vercel.app"}):
        app = create_app("testing")
        c = app.test_client()
        r = c.options("/api/health", headers={"Origin": "https://x.vercel.app"})
        assert r.status_code == 200
        assert r.headers["Access-Control-Allow-Origin"] == "https://x.vercel.app"
        r = c.get("/api/health", headers={"Origin": "https://x.vercel.app"})
        assert r.headers["Access-Control-Allow-Origin"] == "https://x.vercel.app"
        # origin tak dikenal → tanpa header CORS
        r = c.get("/api/health", headers={"Origin": "https://evil.example"})
        assert "Access-Control-Allow-Origin" not in r.headers
