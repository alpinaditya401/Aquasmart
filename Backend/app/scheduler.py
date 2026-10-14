"""Job terjadwal: expire_pending_commands.

Command berstatus 'pending' yang lebih tua dari COMMAND_EXPIRY_MINUTES
(default 10) diubah menjadi 'expired' agar tidak menumpuk di antrian
dan tidak bisa di-poll selamanya oleh firmware.

Dijalankan via:
- Flask CLI:  flask expire-commands
- Scheduler:  hanya aktif bila SCHEDULER_ENABLED=true (mencegah job
  dobel saat multi-worker gunicorn).
"""
import logging
import os
import time

log = logging.getLogger(__name__)


def expire_pending_commands():
    """Return jumlah command yang diubah menjadi 'expired'."""
    from app import db
    from app.models import ActuatorCommand

    try:
        minutes = int(os.environ.get("COMMAND_EXPIRY_MINUTES", "10"))
    except ValueError:
        minutes = 10
    cutoff = int(time.time()) - minutes * 60
    updated = (ActuatorCommand.query
               .filter(ActuatorCommand.status == "pending",
                       ActuatorCommand.created_at < cutoff)
               .update({ActuatorCommand.status: "expired"},
                       synchronize_session=False))
    db.session.commit()
    return updated


def start_scheduler(app, interval_minutes=1):
    """Jalankan BackgroundScheduler (daemon) di dalam proses ini."""
    from apscheduler.schedulers.background import BackgroundScheduler

    def _run():
        with app.app_context():
            n = expire_pending_commands()
            if n:
                log.warning("scheduler: %d command expired", n)

    sched = BackgroundScheduler(daemon=True)
    sched.add_job(_run, "interval", minutes=interval_minutes,
                  id="expire_pending_commands", replace_existing=True,
                  max_instances=1, coalesce=True)
    sched.start()
    app.extensions["scheduler"] = sched
    log.warning("scheduler aktif: expire_pending_commands tiap %d menit",
                interval_minutes)
    return sched
