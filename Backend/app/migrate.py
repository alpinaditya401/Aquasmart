"""Migrasi aditif ringan — hanya TAMBAH kolom yang belum ada.

Dijalankan saat boot (wsgi.py). Idempoten: aman dijalankan berulang,
kompatibel SQLite dan Postgres. Tidak pernah menghapus/mengubah kolom.
"""
import logging

from sqlalchemy import inspect, text

log = logging.getLogger(__name__)

# (tabel, kolom, definisi SQL)
ADDITIVE_COLUMNS = [
    ("alerts", "acknowledged_by", "INTEGER"),
    ("device_telemetry", "source", "TEXT"),
]


def ensure_columns(db):
    """Tambahkan kolom yang belum ada; backfill source='simulated'."""
    engine = db.engine
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table, column, ddl in ADDITIVE_COLUMNS:
            if table not in existing_tables:
                continue
            cols = {c["name"] for c in insp.get_columns(table)}
            if column not in cols:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
                log.warning("migrasi: kolom %s.%s ditambahkan", table, column)
        # Backfill sekali jalan: semua telemetri existing = 'simulated'.
        if "device_telemetry" in existing_tables:
            cols = {c["name"] for c in insp.get_columns("device_telemetry")}
            if "source" in cols:
                n = conn.execute(text(
                    "UPDATE device_telemetry SET source='simulated' "
                    "WHERE source IS NULL")).rowcount
                if n:
                    log.warning("migrasi: %d baris device_telemetry "
                                "di-backfill source='simulated'", n)
        # Commands from the dashboard used to be stored as 'dashboard', which
        # is outside the provenance set the frontend accepts.
        if "actuator_commands" in existing_tables:
            n = conn.execute(text(
                "UPDATE actuator_commands SET provenance='manual' "
                "WHERE provenance='dashboard'")).rowcount
            if n:
                log.warning("migrasi: %d command provenance 'dashboard' "
                            "diganti 'manual'", n)
