"""SQLite storage."""

import json
import os
import sqlite3
import threading
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL DEFAULT '',
    pw_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
    can_apply INTEGER NOT NULL DEFAULT 1,
    disabled INTEGER NOT NULL DEFAULT 0,
    must_change_pw INTEGER NOT NULL DEFAULT 0,
    failed_logins INTEGER NOT NULL DEFAULT 0,
    locked_until REAL NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    last_login REAL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    csrf TEXT NOT NULL,
    created_at REAL NOT NULL,
    last_seen REAL NOT NULL,
    expires_at REAL NOT NULL,
    ip TEXT,
    user_agent TEXT
);

CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);

-- one Journaline service = one packet-mode data service with its own output file
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    output_path TEXT NOT NULL DEFAULT '',
    bitrate INTEGER NOT NULL DEFAULT 8,
    packet_address INTEGER NOT NULL DEFAULT 1,
    write_mode TEXT NOT NULL DEFAULT 'inplace',
    datagroup_mode INTEGER NOT NULL DEFAULT 0,
    toc_enabled INTEGER NOT NULL DEFAULT 1,
    toc_timeout INTEGER NOT NULL DEFAULT 0,
    compression TEXT NOT NULL DEFAULT 'auto',
    weights TEXT NOT NULL DEFAULT '{}',
    mux TEXT NOT NULL DEFAULT '{}',
    revisions TEXT NOT NULL DEFAULT '{}',
    sort INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS objects (
    id INTEGER PRIMARY KEY,
    service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    jid INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('menu', 'text', 'title', 'list')),
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    items TEXT NOT NULL DEFAULT '[]',
    rows TEXT NOT NULL DEFAULT '[]',
    static INTEGER NOT NULL DEFAULT 0,
    compression TEXT NOT NULL DEFAULT '',
    repeat INTEGER NOT NULL DEFAULT 0,
    expires TEXT NOT NULL DEFAULT '',
    lifetime INTEGER NOT NULL DEFAULT 0,
    language TEXT NOT NULL DEFAULT '',
    links TEXT NOT NULL DEFAULT '[]',
    note TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    UNIQUE (service_id, jid)
);

-- RSS/Atom feeds; each feed is an object in the tree (jid) whose content is generated
CREATE TABLE IF NOT EXISTS feeds (
    id INTEGER PRIMARY KEY,
    service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    jid INTEGER NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('menu', 'ticker', 'list')),
    title TEXT NOT NULL DEFAULT '',
    max_items INTEGER NOT NULL DEFAULT 10,
    item_text TEXT NOT NULL DEFAULT 'description',
    show_time INTEGER NOT NULL DEFAULT 0,
    static INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,
    items TEXT NOT NULL DEFAULT '[]',
    id_map TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT '',
    checked_at REAL,
    content_hash TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    UNIQUE (service_id, jid)
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY,
    created_at REAL NOT NULL,
    user_id INTEGER,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS builds (
    id INTEGER PRIMARY KEY,
    started_at REAL NOT NULL,
    finished_at REAL,
    trigger TEXT NOT NULL,
    user_id INTEGER,
    username TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'running',
    message TEXT NOT NULL DEFAULT '',
    stats TEXT NOT NULL DEFAULT '{}',
    warnings TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY,
    ts REAL NOT NULL,
    user_id INTEGER,
    username TEXT NOT NULL DEFAULT '',
    ip TEXT NOT NULL DEFAULT '',
    action TEXT NOT NULL,
    target TEXT NOT NULL DEFAULT '',
    details TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS audit_ts ON audit(ts);
"""

DEFAULT_SETTINGS = {
    "mux_name": "",
    "ensemble": {"ecc": "", "eid": ""},
    "refresh_minutes": 15,
    "timezone": "",
    "allow_private_urls": False,
    "session_hours": 12,
    "setup_complete": False,
    "dismissed_warnings": {},
}

_local = threading.local()
_path = None


def init(data_dir):
    global _path
    os.makedirs(data_dir, mode=0o750, exist_ok=True)
    _path = os.path.join(data_dir, "odr-journaline.db")
    c = conn()
    c.executescript(SCHEMA)
    for k, v in DEFAULT_SETTINGS.items():
        c.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (k, json.dumps(v)))
    try:
        os.chmod(_path, 0o600)
    except OSError:
        pass


def conn() -> sqlite3.Connection:
    c = getattr(_local, "conn", None)
    if c is None or getattr(_local, "path", None) != _path:
        c = sqlite3.connect(_path, timeout=30, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")
        c.execute("PRAGMA journal_mode = WAL")
        c.execute("PRAGMA busy_timeout = 30000")
        _local.conn = c
        _local.path = _path
    return c


def q(sql, args=()):
    return [dict(r) for r in conn().execute(sql, args).fetchall()]


def q1(sql, args=()):
    r = conn().execute(sql, args).fetchone()
    return dict(r) if r else None


def x(sql, args=()):
    return conn().execute(sql, args)


class transaction:
    def __enter__(self):
        conn().execute("BEGIN IMMEDIATE")
        return conn()

    def __exit__(self, exc_type, *_):
        conn().execute("ROLLBACK" if exc_type else "COMMIT")
        return False


def get_setting(key):
    r = q1("SELECT value FROM settings WHERE key = ?", (key,))
    if r is None:
        return DEFAULT_SETTINGS.get(key)
    return json.loads(r["value"])


def all_settings():
    out = dict(DEFAULT_SETTINGS)
    for r in q("SELECT key, value FROM settings"):
        out[r["key"]] = json.loads(r["value"])
    return out


def set_setting(key, value):
    x("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
      (key, json.dumps(value)))


def get_meta(key, default=None):
    r = q1("SELECT value FROM meta WHERE key = ?", (key,))
    return r["value"] if r else default


def set_meta(key, value):
    x("INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
      (key, str(value)))


def mark_dirty():
    set_meta("dirty_since", get_meta("dirty_since") or time.time())


def audit(user, ip, action, target="", details=None):
    x("INSERT INTO audit(ts, user_id, username, ip, action, target, details) VALUES (?,?,?,?,?,?,?)",
      (time.time(), user["id"] if user else None, user["username"] if user else "", ip or "",
       action, target, json.dumps(details or {})))
