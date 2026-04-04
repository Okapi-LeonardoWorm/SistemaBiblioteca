import threading
import time
from datetime import datetime

from flask import Flask

from app.services.backup_service import (
    cleanup_expired_local_backups,
    process_due_schedules_once,
    process_pending_drive_uploads_once,
)

_runtime_lock = threading.Lock()
_runtime_started = False
_runtime_thread = None


def _loop(app: Flask):
    interval_seconds = int(app.config.get('BACKUP_RUNTIME_LOOP_SECONDS', 30) or 30)

    while True:
        try:
            with app.app_context():
                process_due_schedules_once()
                process_pending_drive_uploads_once(limit=5)
                cleanup_expired_local_backups()
        except Exception:
            # Mantém o loop vivo; erros são refletidos no status de runs/uploads.
            pass

        time.sleep(max(5, interval_seconds))


def start_backup_runtime(app: Flask):
    global _runtime_started, _runtime_thread

    if not app.config.get('BACKUP_RUNTIME_ENABLED', True):
        return

    with _runtime_lock:
        if _runtime_started:
            return

        _runtime_thread = threading.Thread(
            target=_loop,
            args=(app,),
            daemon=True,
            name='backup-runtime-worker',
        )
        _runtime_thread.start()
        _runtime_started = True
