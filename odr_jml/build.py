"""Snapshots, feed refresh and carousel generation for every Journaline service."""

import hashlib
import json
import logging
import os
import secrets
import stat
import threading
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import db, feeds, fetch
from .encoder import jml, service as svc

log = logging.getLogger("odr_jml.build")

BITRATES = tuple(range(8, 97, 8))
SLOW_CYCLE = "slow_cycle"
SLOW_CYCLE_SECONDS = 120
_lock = threading.Lock()
_state = {"running": False, "build_id": None}

OBJECT_FIELDS = ("jid", "type", "title", "body", "items", "rows", "static", "compression", "repeat", "expires",
                 "lifetime", "language", "links", "note")
FEED_FIELDS = ("id", "jid", "name", "url", "mode", "title", "max_items", "item_text", "show_time", "static", "enabled")
SERVICE_FIELDS = ("id", "name", "provider", "enabled", "output_path", "bitrate", "packet_address", "write_mode",
                  "datagroup_mode", "toc_enabled", "toc_timeout", "compression", "weights", "mux")


def fmt_duration(seconds):
    m, s = divmod(int(round(seconds)), 60)
    return f"{m} min {s} s" if m else f"{s} s"


def warning_key(text):
    if text.startswith("Carousel takes ") or " carousel takes " in text:
        return SLOW_CYCLE + ":" + text.split(":")[0]
    return "w:" + hashlib.sha1(text.encode()).hexdigest()[:16]


def split_dismissed(warnings, stats):
    dismissed = db.get_setting("dismissed_warnings") or {}
    keep, hidden = [], []
    cycles = {s["name"]: s.get("cycle_seconds", 0) for s in stats.get("services", [])}
    for w in warnings:
        key = warning_key(w)
        if key in dismissed:
            if key.startswith(SLOW_CYCLE):
                name = key.split(":", 1)[1]
                if cycles.get(name, 0) > float(dismissed[key]) * 1.25:
                    keep.append(w)
                    continue
            hidden.append(w)
        else:
            keep.append(w)
    return keep, hidden


def get_tz(name):
    if name:
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return datetime.now().astimezone().tzinfo


def valid_tz(name):
    if not name:
        return True
    try:
        ZoneInfo(name)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False


# --- model -> encoder dicts -------------------------------------------------------------

def object_row_to_dict(o):
    """DB/snapshot object row -> encoder object dict."""
    out = {"id": o["jid"], "type": o["type"], "title": o["title"], "static": bool(o["static"])}
    items = o["items"] if isinstance(o["items"], list) else json.loads(o["items"] or "[]")
    rows = o["rows"] if isinstance(o["rows"], list) else json.loads(o["rows"] or "[]")
    links = o["links"] if isinstance(o["links"], list) else json.loads(o["links"] or "[]")
    if o["type"] == "menu":
        out["items"] = [{"target": int(i["target"]), "label": i["label"]} for i in items]
    elif o["type"] == "text":
        out["body"] = o["body"]
    elif o["type"] == "list":
        out["rows"] = rows
    if o.get("compression"):
        out["compression"] = o["compression"]
    if o.get("repeat"):
        out["repeat"] = int(o["repeat"])
    if o.get("expires"):
        out["expires"] = o["expires"]
    if o.get("lifetime"):
        out["lifetime"] = int(o["lifetime"])
    if o.get("language"):
        out["language"] = o["language"]
    if links:
        out["links"] = links
    return out


def service_objects(service, now=None, tz=None):
    """All encoder object dicts of a service (manual objects + feeds), with
    objects past their absolute expiry left out (and links to them removed).
    `service` has "objects" (rows) and "feeds" (rows with current items/id_map).
    Returns (objects, notes)."""
    now = now or datetime.now(timezone.utc)
    tz = tz or timezone.utc
    objs = [object_row_to_dict(o) for o in service["objects"]]
    for f in service["feeds"]:
        if f.get("enabled", 1):
            objs += feeds.objects(f, tz)
    notes = []
    expired = set()
    for o in objs:
        if o.get("expires") and o["id"] != 0:
            try:
                when = datetime.fromisoformat(o["expires"].replace("Z", "+00:00"))
                if when.tzinfo is None:
                    when = when.replace(tzinfo=tz)
                if when <= now:
                    expired.add(o["id"])
            except ValueError:
                pass
    while expired:
        objs = [o for o in objs if o["id"] not in expired]
        notes += [f"object 0x{i:04X} has expired and is no longer broadcast" for i in sorted(expired)]
        expired = set()
        for o in objs:
            if o["type"] == "menu":
                before = len(o["items"])
                o["items"] = [i for i in o["items"] if i["target"] in {x["id"] for x in objs}]
                if before and not o["items"] and o["id"] != 0:
                    expired.add(o["id"])
    return objs, notes


# --- snapshot ---------------------------------------------------------------------------

def current_state():
    services = db.q("SELECT * FROM services ORDER BY sort, id")
    objs = db.q("SELECT * FROM objects ORDER BY service_id, jid")
    fds = db.q("SELECT * FROM feeds ORDER BY service_id, jid")
    out = []
    for s in services:
        d = {k: s[k] for k in SERVICE_FIELDS}
        d["weights"] = json.loads(s["weights"])
        d["mux"] = json.loads(s["mux"])
        d["objects"] = [{k: o[k] for k in OBJECT_FIELDS} for o in objs if o["service_id"] == s["id"]]
        d["feeds"] = [{k: f[k] for k in FEED_FIELDS} for f in fds if f["service_id"] == s["id"]]
        out.append(d)
    settings = db.all_settings()
    return {"services": out, "settings": {"timezone": settings["timezone"]}}


def latest_snapshot():
    r = db.q1("SELECT * FROM snapshots ORDER BY id DESC LIMIT 1")
    return json.loads(r["data"]) if r else None


def save_snapshot(user):
    data = current_state()
    db.x("INSERT INTO snapshots(created_at, user_id, data) VALUES (?,?,?)",
         (time.time(), user["id"] if user else None, json.dumps(data)))
    db.x("DELETE FROM snapshots WHERE id NOT IN (SELECT id FROM snapshots ORDER BY id DESC LIMIT 20)")
    db.set_meta("dirty_since", "")
    return data


def _attach_feed_items(service):
    """Feeds in a snapshot follow the latest successfully fetched items."""
    cur = {f["id"]: f for f in db.q("SELECT id, items, id_map FROM feeds WHERE service_id = ?", (service["id"],))}
    for f in service["feeds"]:
        c = cur.get(f["id"])
        f["items"] = json.loads(c["items"]) if c else []
        f["id_map"] = {k: int(v) for k, v in json.loads(c["id_map"]).items()} if c else {}


# --- feed refresh -----------------------------------------------------------------------

def used_ids(service_id, exclude_feed=None):
    ids = {r["jid"] for r in db.q("SELECT jid FROM objects WHERE service_id = ?", (service_id,))}
    for f in db.q("SELECT id, jid, id_map FROM feeds WHERE service_id = ?", (service_id,)):
        ids.add(f["jid"])
        if f["id"] != exclude_feed:
            ids.update(int(v) for v in json.loads(f["id_map"]).values())
    return ids


def refresh_feed(feed, allow_private):
    """Fetch and parse one feed; on failure keep the previous items. Returns
    (error text or '', changed)."""
    now = time.time()
    try:
        data, _, _ = fetch.fetch(feed["url"], allow_private=allow_private, max_bytes=10 * 1024 * 1024,
                                 accept="application/rss+xml, application/atom+xml, application/xml, text/xml")
        parsed = feeds.parse(data)
        items = parsed["items"][:feeds.MAX_ITEMS]
        f = dict(feed, items=items, id_map={k: int(v) for k, v in json.loads(feed["id_map"]).items()})
        id_map = feeds.assign_ids(f, used_ids(feed["service_id"], exclude_feed=feed["id"]))
        h = feeds.content_hash([items[:feed["max_items"]], id_map])
        changed = h != feed["content_hash"]
        db.x("UPDATE feeds SET items=?, id_map=?, status=?, checked_at=?, content_hash=? WHERE id=?",
             (json.dumps(items), json.dumps(id_map), f"ok: {len(items)} items", now, h, feed["id"]))
        return "", changed
    except (fetch.FetchError, feeds.FeedError) as e:
        msg = str(e)[:300]
    except Exception as e:  # anything a hostile feed can trigger
        msg = f"{e.__class__.__name__}: {str(e)[:250]}"
    db.x("UPDATE feeds SET status=?, checked_at=? WHERE id=?", ("error: " + msg, now, feed["id"]))
    return msg, False


def refresh_all():
    """Fetch every enabled feed. Returns (warnings, any_changed)."""
    allow_private = bool(db.get_setting("allow_private_urls"))
    warnings, changed = [], False
    for f in db.q("SELECT f.*, s.name AS service_name FROM feeds f JOIN services s ON s.id = f.service_id "
                  "WHERE f.enabled = 1"):
        err, ch = refresh_feed(f, allow_private)
        changed = changed or ch
        if err:
            warnings.append(f"{f['service_name']}: feed \"{f['name'] or f['url'][:60]}\": {err} - kept previous items")
    return warnings, changed


# --- generation -------------------------------------------------------------------------

def generate_service(service, previous_revisions, now=None, tz=None):
    """Encode one service. Returns (stream, result, warnings). Raises ValueError
    with all problems when the service cannot be broadcast."""
    objs, notes = service_objects(service, now, tz)
    errors, warns = svc.validate(objs)
    label = service["name"]
    fmt = lambda oid, m: f"{label}: " + (f"object 0x{oid:04X} " if oid is not None else "") + m
    if errors:
        raise ValueError("; ".join(fmt(i, m) for i, m in errors[:20]))
    try:
        res = svc.build(objs, revisions=previous_revisions, weights=service.get("weights"),
                        toc_enabled=bool(service["toc_enabled"]), toc_timeout=int(service["toc_timeout"] or 0),
                        compression=service.get("compression") or "auto")
    except jml.EncodeError as e:
        raise ValueError(f"{label}: {e}")
    bitrate = int(service["bitrate"])
    stream = svc.stream(res["groups"], bitrate, int(service["packet_address"]), bool(service["datagroup_mode"]))
    cycle = round(len(stream) * 8 / (bitrate * 1000), 1)
    warnings = [fmt(i, m) for i, m in warns] + [f"{label}: {n}" for n in notes]
    by_type = {}
    for o in res["objects"]:
        t = by_type.setdefault(o["type"], {"count": 0, "bytes": 0, "repeats": 0})
        t["count"] += 1
        t["bytes"] += o["bytes"]
        t["repeats"] = max(t["repeats"], o["repeats"])
    stats = {
        "id": service["id"], "name": label, "objects": len(objs), "stream_bytes": len(stream),
        "payload_bytes": res["stats"]["payload_bytes"], "toc_bytes": res["stats"]["toc_bytes"],
        "datagroups": res["stats"]["datagroups"], "bitrate": bitrate, "cycle_seconds": cycle,
        "by_type": by_type, "toc_revision": res["stats"]["toc_revision"],
        "largest": sorted(({"id": o["id"], "type": o["type"], "bytes": o["bytes"]} for o in res["objects"]),
                          key=lambda x: -x["bytes"])[:5],
        "wait": {t: round(cycle / max(1, v["repeats"]), 1) for t, v in by_type.items()},
        "output_path": service["output_path"],
    }
    if cycle > SLOW_CYCLE_SECONDS:
        warnings.append(f"{label}: carousel takes {fmt_duration(cycle)} to cycle at {bitrate} kbps - consider a "
                        "higher bitrate, fewer feed items or fewer repeats")
    return stream, res, stats, warnings


def check_output_path(path):
    if not path or not os.path.isabs(path):
        raise ValueError("Output path must be an absolute path.")
    if not path.endswith(".dat"):
        raise ValueError("Output file name must end in .dat")
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        raise ValueError(f"Directory {parent} does not exist.")
    if os.path.lexists(path):
        st = os.lstat(path)
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            raise ValueError("Output path exists and is not a regular file (symlinks are refused).")
    if not os.access(parent, os.W_OK) and not (os.path.exists(path) and os.access(path, os.W_OK)):
        raise ValueError(f"The service user cannot write to {parent}.")


def write_output(path, stream, mode):
    check_output_path(path)
    if mode == "atomic":
        tmp = os.path.join(os.path.dirname(path), f".{os.path.basename(path)}.{secrets.token_hex(4)}.tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(fd, "wb") as f:
            os.fchmod(f.fileno(), 0o644)  # odr-dabmux usually runs as another user
            f.write(stream)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    else:
        # in place: ODR-DabMux keeps the file open and rewinds at EOF, so the
        # same inode must be rewritten for it to pick up the new carousel
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o644)
        with os.fdopen(fd, "wb") as f:
            os.fchmod(f.fileno(), 0o644)
            f.write(stream)
            f.truncate()
            f.flush()
            os.fsync(f.fileno())


def _output_conflicts(services):
    seen = {}
    out = []
    for s in services:
        p = s["output_path"]
        if p and p in seen:
            out.append(f"{s['name']} and {seen[p]} write to the same file {p}")
        seen[p] = s["name"]
    return out


# --- orchestration ----------------------------------------------------------------------

def status():
    return dict(_state)


def run(trigger, user=None, apply_changes=False, refresh=True):
    """Run a build synchronously. Returns the build row id."""
    if not _lock.acquire(blocking=False):
        raise RuntimeError("A build is already running.")
    try:
        _state.update(running=True)
        bid = db.x("INSERT INTO builds(started_at, trigger, user_id, username) VALUES (?,?,?,?)",
                   (time.time(), trigger, user["id"] if user else None, user["username"] if user else "")).lastrowid
        _state["build_id"] = bid
        warnings, errors, svc_stats = [], [], []
        try:
            if refresh:
                warnings += refresh_all()[0]
            if apply_changes:
                snap = save_snapshot(user)
            else:
                snap = latest_snapshot()
                if snap is None:
                    raise ValueError("Nothing has been applied yet.")
            tz = get_tz(snap["settings"].get("timezone"))
            live = [s for s in snap["services"] if s["enabled"]]
            if not live:
                raise ValueError("No enabled Journaline services.")
            conflicts = _output_conflicts(live)
            if conflicts:
                raise ValueError("; ".join(conflicts))
            written = 0
            for s in live:
                _attach_feed_items(s)
                row = db.q1("SELECT revisions FROM services WHERE id = ?", (s["id"],))
                prev = json.loads(row["revisions"]) if row else {}
                try:
                    stream, res, stats, w = generate_service(s, prev, tz=tz)
                    write_output(s["output_path"], stream, s.get("write_mode") or "inplace")
                except (ValueError, OSError) as e:
                    errors.append(str(e) if str(e).startswith(s["name"]) else f"{s['name']}: {e}")
                    continue
                if row:
                    db.x("UPDATE services SET revisions = ? WHERE id = ?", (json.dumps(res["revisions"]), s["id"]))
                warnings += w
                svc_stats.append(stats)
                written += 1
            stats = {"services": svc_stats, "stream_bytes": sum(s["stream_bytes"] for s in svc_stats),
                     "objects": sum(s["objects"] for s in svc_stats)}
            warnings, hidden = split_dismissed(warnings, stats)
            stats["dismissed_warnings"] = len(hidden)
            if errors:
                status_ = "error"
                msg = (f"Wrote {written} of {len(live)} service(s). " if written else "Nothing written. ") \
                    + " | ".join(errors)
            else:
                status_ = "warning" if warnings else "ok"
                msg = f"Wrote {len(live)} service(s), {stats['stream_bytes']:,} bytes"
            db.x("UPDATE builds SET finished_at=?, status=?, message=?, stats=?, warnings=? WHERE id=?",
                 (time.time(), status_, msg[:2000], json.dumps(stats), json.dumps(warnings[:200]), bid))
            if written:
                db.set_meta("last_success", time.time())
        except Exception as e:
            log.exception("build failed")
            msg = str(e) if isinstance(e, (ValueError, OSError)) else f"{e.__class__.__name__}: {e}"
            db.x("UPDATE builds SET finished_at=?, status='error', message=?, warnings=? WHERE id=?",
                 (time.time(), msg[:2000], json.dumps(warnings[:200]), bid))
        db.x("DELETE FROM builds WHERE id NOT IN (SELECT id FROM builds ORDER BY id DESC LIMIT 500)")
        return bid
    finally:
        _state.update(running=False)
        _lock.release()


def run_async(trigger, user=None, apply_changes=False):
    if _state["running"]:
        raise RuntimeError("A build is already running.")
    t = threading.Thread(target=run, args=(trigger, user, apply_changes), daemon=True)
    t.start()


def preview(service_id):
    """Encode the current (unapplied) state of one service and decode it back,
    as a receiver would see it. Never writes anything."""
    from .encoder import decode
    state = current_state()
    s = next((x for x in state["services"] if x["id"] == service_id), None)
    if s is None:
        raise ValueError("Service not found.")
    _attach_feed_items(s)
    tz = get_tz(db.get_setting("timezone"))
    objs, notes = service_objects(s, tz=tz)
    errors, warns = svc.validate(objs)
    decoded, enc_errors = {}, []
    row = db.q1("SELECT revisions FROM services WHERE id = ?", (service_id,))
    prev = json.loads(row["revisions"]) if row else {}
    revs = svc.next_revisions(objs, prev)
    for o in objs:
        try:
            b = jml.encode(o, revs[str(o["id"])]["rev"], o.get("compression") or s.get("compression") or "auto")
            d = decode.decode(b)
            d["plain_bytes"] = 3 + len(jml.content(o))
            decoded[o["id"]] = d
        except (jml.EncodeError, decode.DecodeError) as e:
            enc_errors.append((o["id"], str(e)))
    depth = svc.hierarchy(objs)
    est = None
    if not errors and not enc_errors:
        try:
            res = svc.build(objs, revisions=prev, weights=s.get("weights"), toc_enabled=bool(s["toc_enabled"]),
                            toc_timeout=int(s["toc_timeout"] or 0), compression=s.get("compression") or "auto")
            stream = svc.stream(res["groups"], int(s["bitrate"]), int(s["packet_address"]), bool(s["datagroup_mode"]))
            est = {"stream_bytes": len(stream), "cycle_seconds": round(len(stream) * 8 / (int(s["bitrate"]) * 1000), 1)}
        except (jml.EncodeError, ValueError) as e:
            enc_errors.append((None, str(e)))
    return {"objects": decoded, "errors": errors + enc_errors, "warnings": warns + [(None, n) for n in notes],
            "depth": depth, "estimate": est}
