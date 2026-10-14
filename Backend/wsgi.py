"""Entry point WSGI — dipakai gunicorn & flask run."""
import os

# Production (Railway): SECRET_KEY wajib dari environment, jangan default dev.
if os.environ.get("FLASK_CONFIG") == "production" and not os.environ.get("SECRET_KEY"):
    raise RuntimeError("SECRET_KEY wajib di-set di environment untuk production.")

from app import create_app, db
from app.migrate import ensure_columns

app = create_app(os.environ.get("FLASK_CONFIG", "default"))

# Pastikan tabel ada saat boot (idempoten — aman untuk SQLite maupun Postgres).
# Dipakai Railway: container baru langsung siap tanpa langkah migrasi manual.
with app.app_context():
    db.create_all()
    ensure_columns(db)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
