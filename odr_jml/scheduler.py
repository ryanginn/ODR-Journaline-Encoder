"""Background job: periodic feed refresh + rebuild, object expiry, and housekeeping."""

import logging
import threading
import time

from . import build, db, security

log = logging.getLogger("odr_jml.scheduler")

_wake = threading.Event()
_next = {"ts": None}


def wake():
    _wake.set()


def next_run_time():
    return _next["ts"]


def tick(now=None):
    """One scheduler pass. Every refresh interval the feeds are re-fetched and,
    if anything was published, the carousel is rebuilt from the last applied
    state - so feed changes and object expiries go on air without an Apply."""
    now = now or time.time()
    minutes = max(5, min(int(db.get_setting("refresh_minutes") or 15), 1440))
    last = float(db.get_meta("last_scheduled") or 0) or None
    if last is None:
        db.set_meta("last_scheduled", now)
        last = now
    _next["ts"] = last + minutes * 60
    if now < _next["ts"]:
        return False
    db.set_meta("last_scheduled", now)
    _next["ts"] = now + minutes * 60
    if build.latest_snapshot() is not None:
        try:
            build.run("scheduled")
        except RuntimeError:
            pass  # a manual build is running; it refreshes too
    else:
        build.refresh_all()
    return True


def loop():
    last_housekeeping = 0
    while True:
        try:
            tick()
            if time.time() - last_housekeeping > 3600:
                last_housekeeping = time.time()
                security.purge_sessions()
                db.x("DELETE FROM audit WHERE ts < ?", (time.time() - 365 * 86400,))
        except Exception:
            log.exception("scheduler error")
        _wake.wait(30)
        _wake.clear()


def start():
    threading.Thread(target=loop, name="scheduler", daemon=True).start()
