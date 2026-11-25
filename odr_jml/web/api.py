"""JSON API."""

import hmac
import json
import os
import re
import secrets
import stat
import time
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, make_response, request

from .. import __version__, build, db, feeds, fetch, muxconf, scheduler, security
from ..encoder import jml, service as svc
from . import COOKIE, ApiError, audit, can_apply, check_service, client_ip, current_user, is_editor, json_body, require

bp = Blueprint("api", __name__)

HEX = lambda n: re.compile(r"^[0-9a-fA-F]{%d}$" % n)
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.@-]{3,64}$")
TYPES = ("menu", "text", "title", "list")
LINK_TYPES = ("url", "phone", "sms", "dab", "jml")


# --- validation helpers -------------------------------------------------------------------

def _str(data, key, maxlen, required=False, label=None, multiline=False):
    v = data.get(key, "")
    if v is None:
        v = ""
    if not isinstance(v, str):
        raise ApiError(f"{label or key} must be text.")
    v = v.replace("\r\n", "\n").strip()
    allowed = "\n\t" if multiline else "\t"
    if "\x00" in v or any(ord(c) < 32 and c not in allowed for c in v):
        raise ApiError(f"{label or key} contains control characters.")
    if len(v) > maxlen:
        raise ApiError(f"{label or key} must be at most {maxlen} characters.")
    if required and not v:
        raise ApiError(f"{label or key} is required.")
    return v


def _int(data, key, lo, hi, label=None):
    try:
        v = int(data.get(key))
    except (TypeError, ValueError):
        raise ApiError(f"{label or key} must be a number.")
    if not lo <= v <= hi:
        raise ApiError(f"{label or key} must be between {lo} and {hi}.")
    return v


def _url(v, label="URL"):
    v = (v or "").strip()
    try:
        fetch.validate_url(v)
    except fetch.FetchError as e:
        raise ApiError(f"{label}: {e}")
    return v


def _jid(v, label="Object ID"):
    if isinstance(v, str):
        s = v.strip().lower()
        try:
            v = int(s, 16) if s.startswith("0x") or re.fullmatch(r"[0-9a-f]*[a-f][0-9a-f]*", s) else int(s)
        except ValueError:
            raise ApiError(f"{label} must be a number, e.g. 0x0012.")
    if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= jml.MAX_FREE_ID:
        raise ApiError(f"{label} must be between 0x0000 and 0xEFFF.")
    return v


# --- session / auth -----------------------------------------------------------------------

def _set_cookie(resp, token, hours):
    resp.set_cookie(COOKIE, token, max_age=int(hours * 3600), httponly=True, samesite="Strict",
                    secure=request.is_secure, path="/")


def _user_public(u):
    return {"id": u["id"], "username": u["username"], "display_name": u["display_name"], "role": u["role"],
            "can_apply": is_editor(u), "must_change_pw": bool(u["must_change_pw"])}


def setup_token_path():
    return os.path.join(current_app.config["ODR_CFG"]["data_dir"], "setup-token")


def users_exist():
    return db.q1("SELECT 1 AS x FROM users LIMIT 1") is not None


def mux_display_name():
    """Shown on the login screen, page title and sidebar. It names the
    multiplex, which is public on air, so it is safe to show before login."""
    return db.get_setting("mux_name") or ""


@bp.get("/api/state")
def state():
    u = current_user()
    return jsonify(
        version=__version__, setup_required=not users_exist(),
        user=_user_public(u) if u else None, csrf=u["csrf"] if u else None,
        setup_complete=bool(db.get_setting("setup_complete")),
        mux_name=mux_display_name(),
    )


@bp.post("/api/setup")
def setup():
    if not security.setup_limiter.hit(client_ip()):
        raise ApiError("Too many attempts - wait 15 minutes.", 429)
    if users_exist():
        raise ApiError("Setup has already been completed.", 409)
    data = json_body()
    token = data.get("token", "")
    try:
        with open(setup_token_path()) as f:
            expected = f.read().strip()
    except OSError:
        raise ApiError("No setup token found. Run: sudo odr-journaline-encoder setup-token", 403)
    if not isinstance(token, str) or not expected or not hmac.compare_digest(token.strip(), expected):
        db.audit(None, client_ip(), "setup.bad_token")
        raise ApiError("Setup token is incorrect.", 403)
    username = _str(data, "username", 64, True, "Username")
    if not USERNAME_RE.match(username):
        raise ApiError("Username may contain letters, digits and . _ @ - (3-64 characters).")
    pw = data.get("password", "")
    problem = security.password_problem(pw, username)
    if problem:
        raise ApiError(problem)
    with db.transaction():
        if users_exist():
            raise ApiError("Setup has already been completed.", 409)
        uid = db.x("INSERT INTO users(username, display_name, pw_hash, role, can_apply, created_at) "
                   "VALUES (?,?,?,?,1,?)", (username, _str(data, "display_name", 64) or username,
                                            security.hash_password(pw), "admin", time.time())).lastrowid
    try:
        os.remove(setup_token_path())
    except OSError:
        pass
    db.audit({"id": uid, "username": username}, client_ip(), "setup.admin_created", username)
    return _login_response(uid)


def _login_response(uid):
    hours = int(db.get_setting("session_hours") or 12)
    token, _ = security.create_session(uid, client_ip(), request.headers.get("User-Agent"), hours)
    db.x("UPDATE users SET last_login = ?, failed_logins = 0, locked_until = 0 WHERE id = ?", (time.time(), uid))
    resp = make_response(jsonify(ok=True))
    _set_cookie(resp, token, hours)
    return resp


@bp.post("/api/login")
def login():
    if not security.login_limiter.hit(client_ip()):
        raise ApiError("Too many login attempts from your address - wait 15 minutes.", 429)
    data = json_body()
    username = data.get("username", "")
    password = data.get("password", "")
    if not isinstance(username, str) or not isinstance(password, str) or len(password) > security.MAX_PASSWORD_LEN:
        raise ApiError("Invalid username or password.", 401)
    u = db.q1("SELECT * FROM users WHERE username = ?", (username.strip(),))
    if not u:
        security.dummy_verify(password)
        db.audit(None, client_ip(), "login.failed", username[:64])
        raise ApiError("Invalid username or password.", 401)
    if u["locked_until"] > time.time():
        security.dummy_verify(password)
        raise ApiError("Account temporarily locked after repeated failures - try again later.", 429)
    if not security.verify_password(password, u["pw_hash"]) or u["disabled"]:
        fails = u["failed_logins"] + 1
        locked = time.time() + security.LOCKOUT_SECONDS if fails >= security.LOCKOUT_THRESHOLD else 0
        db.x("UPDATE users SET failed_logins = ?, locked_until = ? WHERE id = ?",
             (0 if locked else fails, locked, u["id"]))
        db.audit(u, client_ip(), "login.failed" + (".locked" if locked else ""), u["username"])
        raise ApiError("Invalid username or password.", 401)
    db.audit(u, client_ip(), "login", u["username"])
    return _login_response(u["id"])


@bp.post("/api/logout")
def logout():
    if g.session_token:
        security.destroy_session(g.session_token)
    resp = make_response(jsonify(ok=True))
    resp.delete_cookie(COOKIE, path="/")
    return resp


@bp.post("/api/account/password")
@require()
def change_password():
    data = json_body()
    u = db.q1("SELECT * FROM users WHERE id = ?", (current_user()["id"],))
    if not security.verify_password(data.get("current", "") or "", u["pw_hash"]):
        raise ApiError("Current password is incorrect.", 403)
    problem = security.password_problem(data.get("new", ""), u["username"])
    if problem:
        raise ApiError(problem)
    if data["new"] == data.get("current"):
        raise ApiError("New password must differ from the current one.")
    db.x("UPDATE users SET pw_hash = ?, must_change_pw = 0 WHERE id = ?",
         (security.hash_password(data["new"]), u["id"]))
    security.destroy_user_sessions(u["id"], except_token=g.session_token)
    audit("account.password_changed", u["username"])
    return jsonify(ok=True)


@bp.patch("/api/account")
@require()
def update_account():
    data = json_body()
    db.x("UPDATE users SET display_name = ? WHERE id = ?", (_str(data, "display_name", 64), current_user()["id"]))
    return jsonify(ok=True)


# --- status / builds ----------------------------------------------------------------------

def _build_public(b):
    return {**b, "stats": json.loads(b["stats"]), "warnings": json.loads(b["warnings"])}


@bp.get("/api/status")
@require()
def status():
    u = current_user()
    last = db.q1("SELECT * FROM builds ORDER BY id DESC LIMIT 1")
    last_ok = db.get_meta("last_success")
    dirty = db.get_meta("dirty_since") or ""
    return jsonify({
        "build": _build_public(last) if last else None,
        "running": build.status()["running"],
        "dirty_since": float(dirty) if dirty else None,
        "published": db.q1("SELECT id FROM snapshots LIMIT 1") is not None,
        "last_success": float(last_ok) if last_ok else None,
        "next_refresh": scheduler.next_run_time(),
        "can_apply": can_apply(u),
        "setup_complete": bool(db.get_setting("setup_complete")),
        "server_time": time.time(),
    })


@bp.get("/api/builds")
@require()
def builds():
    return jsonify([_build_public(r) for r in db.q("SELECT * FROM builds ORDER BY id DESC LIMIT 50")])


@bp.post("/api/builds/<int:bid>/dismiss")
@require("editor")
def dismiss_warnings(bid):
    b = db.q1("SELECT * FROM builds WHERE id = ?", (bid,))
    if not b:
        raise ApiError("Build not found.", 404)
    text = json_body().get("warning")
    warnings = json.loads(b["warnings"])
    stats = json.loads(b["stats"])
    targets = warnings if text is None else [w for w in warnings if w == text]
    if not targets:
        raise ApiError("Warning not found.", 404)
    dismissed = dict(db.get_setting("dismissed_warnings") or {})
    cycles = {s["name"]: s.get("cycle_seconds", 0) for s in stats.get("services", [])}
    for w in targets:
        key = build.warning_key(w)
        dismissed[key] = cycles.get(key.split(":", 1)[1], 0) if key.startswith(build.SLOW_CYCLE) else 1
    if len(dismissed) > 1000:
        raise ApiError("Too many dismissed warnings - restore them first.")
    db.set_setting("dismissed_warnings", dismissed)
    remaining = [w for w in warnings if w not in targets]
    stats["dismissed_warnings"] = stats.get("dismissed_warnings", 0) + len(targets)
    status_ = "ok" if b["status"] == "warning" and not remaining else b["status"]
    db.x("UPDATE builds SET warnings = ?, stats = ?, status = ? WHERE id = ?",
         (json.dumps(remaining), json.dumps(stats), status_, bid))
    audit("warnings.dismiss", str(bid), {"count": len(targets)})
    return jsonify(ok=True)


@bp.post("/api/warnings/restore")
@require("editor")
def restore_warnings():
    db.set_setting("dismissed_warnings", {})
    audit("warnings.restore")
    return jsonify(ok=True)


@bp.post("/api/apply")
@require("editor")
def apply():
    u = current_user()
    live = db.q("SELECT * FROM services WHERE enabled = 1")
    if not live:
        raise ApiError("There is no enabled Journaline service to publish.")
    for s in live:
        try:
            build.check_output_path(s["output_path"])
        except ValueError as e:
            raise ApiError(f"{s['name']}: output location problem: {e}")
    try:
        build.run_async("apply", u, apply_changes=True)
    except RuntimeError as e:
        raise ApiError(str(e), 409)
    audit("apply")
    return jsonify(ok=True)


# --- ensemble (for default service ids) ---------------------------------------------------

def _ensemble(data):
    ecc = _str(data, "ecc", 4, False, "ECC").lower().removeprefix("0x")
    eid = _str(data, "eid", 6, False, "EId").lower().removeprefix("0x")
    if ecc and not HEX(2).match(ecc):
        raise ApiError("ECC must be 2 hex digits, e.g. e1.")
    if eid and not HEX(4).match(eid):
        raise ApiError("EId must be 4 hex digits, e.g. c185.")
    return {"ecc": ecc, "eid": eid}


@bp.post("/api/mux/read")
@require("editor")
def read_mux_config():
    """Read an odr-dabmux config (.mux/.info or .json) uploaded or (admin) on the server."""
    if "file" in request.files:
        data = request.files["file"].read(2 * 1024 * 1024 + 1)
        name = request.files["file"].filename or "upload"
    elif request.form.get("path"):
        if current_user()["role"] != "admin":
            raise ApiError("Only administrators can read files on the server.", 403)
        path = os.path.realpath(request.form["path"])
        try:
            st = os.stat(path)
            if not stat.S_ISREG(st.st_mode) or st.st_size > 2 * 1024 * 1024:
                raise ApiError("Not a regular file of at most 2 MB.")
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            raise ApiError(f"Cannot read {path}: {e.strerror}")
        name = path
    else:
        raise ApiError("Upload a config file or choose one on the server.")
    if len(data) > 2 * 1024 * 1024:
        raise ApiError("Config file is too large.")
    try:
        info = muxconf.read_config(data)
    except ValueError as e:
        raise ApiError(f"Could not read the config: {e}")
    if request.form.get("save_ensemble") == "1" and info["ensemble"]["ecc"] and info["ensemble"]["eid"]:
        db.set_setting("ensemble", {"ecc": info["ensemble"]["ecc"], "eid": info["ensemble"]["eid"]})
        if not db.get_setting("mux_name") and info["ensemble"]["label"]:
            db.set_setting("mux_name", info["ensemble"]["label"][:64])
    if request.form.get("save_ensemble") == "1":
        db.set_setting("mux_services", info["service_list"])
    audit("mux.read", name[:200])
    return jsonify(info)


# --- services -----------------------------------------------------------------------------

SERVICE_DEFAULT_WEIGHTS = dict(svc.DEFAULT_WEIGHTS)


def _service_fields(data, creating=False):
    out = {}
    if "name" in data or creating:
        out["name"] = _str(data, "name", 64, True, "Name")
    if "provider" in data:
        out["provider"] = _str(data, "provider", 64, False, "Provider")
    if "enabled" in data:
        out["enabled"] = 1 if data["enabled"] else 0
    if "output_path" in data:
        p = _str(data, "output_path", 1024, False, "Output path")
        if p:
            try:
                build.check_output_path(p)
            except ValueError as e:
                raise ApiError(str(e))
            clash = db.q1("SELECT name FROM services WHERE output_path = ? AND id != ?", (p, data.get("_id") or 0))
            if clash:
                raise ApiError(f"{clash['name']} already writes to that file - each service needs its own.")
        out["output_path"] = p
    if "bitrate" in data:
        b = _int(data, "bitrate", 8, 96, "Bitrate")
        if b not in build.BITRATES:
            raise ApiError("Bitrate must be a multiple of 8 kbps, from 8 to 96.")
        out["bitrate"] = b
    if "packet_address" in data:
        out["packet_address"] = _int(data, "packet_address", 1, 1023, "Packet address")
    if "write_mode" in data:
        if data["write_mode"] not in ("inplace", "atomic"):
            raise ApiError("Invalid write mode.")
        out["write_mode"] = data["write_mode"]
    for k in ("datagroup_mode", "toc_enabled"):
        if k in data:
            out[k] = 1 if data[k] else 0
    if "toc_timeout" in data:
        out["toc_timeout"] = _int(data, "toc_timeout", 0, 65535, "Service timeout")
    if "compression" in data:
        if data["compression"] not in ("auto", "off"):
            raise ApiError("Compression must be auto or off.")
        out["compression"] = data["compression"]
    if "weights" in data:
        w = data["weights"]
        if not isinstance(w, dict):
            raise ApiError("Invalid repeat settings.")
        out["weights"] = json.dumps({k: _int(w, k, 0 if k == "root_bonus" else 1, 20, f"Repeats for {k}")
                                     for k in SERVICE_DEFAULT_WEIGHTS if k in w})
    if "mux" in data:
        out["mux"] = json.dumps(_mux_fields(data["mux"]))
    return out


def _mux_fields(m):
    if not isinstance(m, dict):
        raise ApiError("Invalid mux settings.")
    ident = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
    ident_long = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
    out = {}
    for k in ("service_uid", "subchannel_uid", "component_uid"):
        v = _str(m, k, 32, True, k)
        if not ident.match(v):
            raise ApiError(f"{k} may only contain letters, digits, - and _.")
        out[k] = v
    sid = _str(m, "service_id", 10, False, "Service id").lower().removeprefix("0x")
    if sid and not HEX(8).match(sid):
        raise ApiError("The service id must be 8 hex digits (32-bit data service id), e.g. e1c185a1.")
    out["service_id"] = sid
    out["label"] = _str(m, "label", 16, True, "Label")
    out["short_label"] = _str(m, "short_label", 8, True, "Short label")
    if any(c in out["label"] + out["short_label"] for c in '"\\'):
        raise ApiError("Labels must not contain quotes or backslashes.")
    out["subchannel_id"] = _int(m, "subchannel_id", 0, 63, "Subchannel id")
    if m.get("protection_profile") not in ("EEP_A", "EEP_B"):
        raise ApiError("Protection profile must be EEP_A or EEP_B.")
    out["protection_profile"] = m["protection_profile"]
    out["protection"] = _int(m, "protection", 1, 4, "Protection level")
    out["dscty"] = _int(m, "dscty", 0, 63, "Component type")
    out["standalone"] = bool(m.get("standalone", True))
    linked = m.get("linked") or []
    if not isinstance(linked, list) or len(linked) > 32:
        raise ApiError("Attach to at most 32 stations.")
    out["linked"] = []
    for l in linked:
        if not isinstance(l, dict):
            raise ApiError("Invalid station.")
        uid = _str(l, "uid", 64, True, "Station uid")
        if not ident_long.match(uid):
            raise ApiError(f"Station uid {uid[:40]} may only contain letters, digits, - and _ "
                           "(use the name from the services section of your odr-dabmux config).")
        if uid in (out["service_uid"],) or any(x["uid"] == uid for x in out["linked"]):
            continue
        out["linked"].append({"uid": uid, "label": _str(l, "label", 64, False, "Station name")})
    return out


def _service_public(s):
    out = dict(s)
    out["weights"] = {**SERVICE_DEFAULT_WEIGHTS, **json.loads(s["weights"])}
    out["mux"] = muxconf.mux_settings({"id": s["id"], "mux": json.loads(s["mux"])})
    out.pop("revisions", None)
    return out


def _live_service(sid):
    """The service's current (unapplied) state, with feed items, for checks."""
    st = build.current_state()
    s = next((x for x in st["services"] if x["id"] == sid), None)
    build._attach_feed_items(s)
    return s


def _summary(s):
    live = _live_service(s["id"])
    try:
        objs, _ = build.service_objects(live, tz=build.get_tz(db.get_setting("timezone")))
        errors, warnings = svc.validate(objs)
    except Exception as e:  # a broken feed must not break the dashboard
        objs, errors, warnings = [], [(None, str(e))], []
    out = _service_public(s)
    out.update(objects=len(live["objects"]), feeds=len(live["feeds"]), broadcast_objects=len(objs),
               errors=[_issue(i, m) for i, m in errors][:20], warnings=[_issue(i, m) for i, m in warnings][:20],
               feed_errors=[f["name"] or f["url"] for f in db.q("SELECT name, url FROM feeds WHERE service_id = ? "
                                                                 "AND status LIKE 'error%'", (s["id"],))])
    last = db.q1("SELECT stats FROM builds WHERE status != 'running' ORDER BY id DESC LIMIT 1")
    out["last_stats"] = next((x for x in json.loads(last["stats"]).get("services", []) if x.get("id") == s["id"]),
                             None) if last else None
    return out


def _issue(oid, msg):
    return {"id": oid, "message": (f"0x{oid:04X} " if oid is not None else "") + msg}


@bp.get("/api/services")
@require()
def list_services():
    return jsonify([_summary(s) for s in db.q("SELECT * FROM services ORDER BY sort, id")])


def next_free_jid(service_id, start=1, stop=feeds.FEED_ID_BASE):
    used = build.used_ids(service_id)
    for i in range(start, stop):
        if i not in used:
            return i
    for i in range(1, jml.MAX_FREE_ID + 1):
        if i not in used:
            return i
    raise ApiError("No free object IDs left in this service.")


def _short_label(name):
    """An 8-character label: the first word if it fits, else the name cut at a word."""
    words = name.split()
    if words and len(words[0]) <= 8:
        out = words[0]
        for w in words[1:]:
            if len(out) + 1 + len(w) > 8:
                break
            out += " " + w
        return out
    return name[:8].strip()


@bp.post("/api/services")
@require("editor")
def create_service():
    data = json_body()
    f = _service_fields(data, creating=True)
    used_addr = {r["packet_address"] for r in db.q("SELECT packet_address FROM services")}
    f.setdefault("packet_address", next(a for a in range(1, 1024) if a not in used_addr))
    f.setdefault("bitrate", 8)
    n = db.q1("SELECT COUNT(*) AS n FROM services")["n"]
    f.setdefault("mux", json.dumps({**muxconf.DEFAULT_MUX, "service_uid": f"srv-journaline{n + 1 if n else ''}",
                                    "subchannel_uid": f"sub-journaline{n + 1 if n else ''}",
                                    "component_uid": f"comp-journaline{n + 1 if n else ''}",
                                    "subchannel_id": 30 + n, "label": f["name"][:16].strip(),
                                    "short_label": _short_label(f["name"])}))
    now = time.time()
    f.update(created_at=now, updated_at=now, sort=n)
    with db.transaction():
        sid = db.x(f"INSERT INTO services({','.join(f)}) VALUES ({','.join('?' * len(f))})",
                   tuple(f.values())).lastrowid
        if data.get("starter", True):
            _insert_object(sid, {"jid": 1, "type": "text", "title": f"Welcome to {f['name']}",
                                 "body": "This is a Journaline text message.\nEdit it, or add menus, lists, "
                                         "news tickers and RSS feeds from the service page.", "static": 1})
            _insert_object(sid, {"jid": 0, "type": "menu", "title": f["name"],
                                 "items": json.dumps([{"target": 1, "label": "Welcome"}]), "static": 1})
    db.mark_dirty()
    audit("service.create", f["name"])
    return jsonify(id=sid)


@bp.get("/api/services/<int:sid>")
@require()
def get_service(sid):
    s = check_service(sid)
    out = _summary(s)
    out["object_list"] = [_object_public(o) for o in db.q("SELECT * FROM objects WHERE service_id = ? ORDER BY jid",
                                                          (sid,))]
    out["feed_list"] = [_feed_public(f) for f in db.q("SELECT * FROM feeds WHERE service_id = ? ORDER BY jid", (sid,))]
    return jsonify(out)


@bp.patch("/api/services/<int:sid>")
@require("editor")
def update_service(sid):
    s = check_service(sid)
    data = json_body()
    data["_id"] = sid
    f = _service_fields(data)
    if f:
        f["updated_at"] = time.time()
        db.x(f"UPDATE services SET {', '.join(k + ' = ?' for k in f)} WHERE id = ?", (*f.values(), sid))
        db.mark_dirty()
    audit("service.update", s["name"], {k: v for k, v in f.items() if k != "updated_at"})
    return jsonify(ok=True)


@bp.delete("/api/services/<int:sid>")
@require("editor")
def delete_service(sid):
    s = check_service(sid)
    db.x("DELETE FROM services WHERE id = ?", (sid,))
    db.mark_dirty()
    audit("service.delete", s["name"])
    return jsonify(ok=True)


@bp.get("/api/services/<int:sid>/preview")
@require()
def preview_service(sid):
    check_service(sid)
    p = build.preview(sid)
    return jsonify(objects={f"{k}": v for k, v in p["objects"].items()},
                   errors=[_issue(i, m) for i, m in p["errors"]], warnings=[_issue(i, m) for i, m in p["warnings"]],
                   depth={str(k): v for k, v in p["depth"].items()}, estimate=p["estimate"])


@bp.get("/api/services/<int:sid>/mux")
@require()
def service_mux(sid):
    s = _service_public(check_service(sid))
    return jsonify(muxconf.snippet(s, db.get_setting("ensemble")))


@bp.get("/api/services/<int:sid>/export")
@require("editor")
def export_service(sid):
    s = _live_service(sid)
    objs = [{k: (json.loads(v) if k in ("items", "rows", "links") else v) for k, v in o.items()} for o in s["objects"]]
    data = {"format": "odr-journaline-encoder/1", "service": {k: s[k] for k in (
        "name", "provider", "bitrate", "toc_enabled", "toc_timeout", "compression", "weights")},
        "objects": objs, "feeds": [{k: f[k] for k in build.FEED_FIELDS if k not in ("id", "items", "id_map")}
                                   for f in s["feeds"]]}
    resp = make_response(json.dumps(data, indent=1, ensure_ascii=False))
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    name = re.sub(r"[^A-Za-z0-9_-]+", "-", s["name"]).strip("-") or "journaline"
    resp.headers["Content-Disposition"] = f'attachment; filename="{name}.json"'
    return resp


@bp.post("/api/services/<int:sid>/import")
@require("editor")
def import_service(sid):
    s = check_service(sid)
    data = json_body()
    doc = data.get("data")
    if not isinstance(doc, dict) or doc.get("format") != "odr-journaline-encoder/1":
        raise ApiError("That isn't an export from this tool.")
    objs, fds = doc.get("objects") or [], doc.get("feeds") or []
    if not isinstance(objs, list) or not isinstance(fds, list) or len(objs) > 5000 or len(fds) > 200:
        raise ApiError("Invalid export file.")
    rows = [_object_fields(o, creating=True) for o in objs]
    feed_rows = [_feed_fields(f, creating=True) for f in fds]
    jids = [r["jid"] for r in rows] + [int(f.get("jid", -1)) for f in fds]
    if len(set(jids)) != len(jids):
        raise ApiError("The export contains duplicate object IDs.")
    with db.transaction():
        db.x("DELETE FROM objects WHERE service_id = ?", (sid,))
        db.x("DELETE FROM feeds WHERE service_id = ?", (sid,))
        for r in rows:
            _insert_object(sid, r)
        for f, raw in zip(feed_rows, fds):
            f["jid"] = _jid(raw.get("jid"))
            _insert_feed(sid, f)
    db.mark_dirty()
    audit("service.import", s["name"], {"objects": len(rows), "feeds": len(feed_rows)})
    return jsonify(objects=len(rows), feeds=len(feed_rows))


# --- objects ------------------------------------------------------------------------------

def _object_public(o):
    out = dict(o)
    for k in ("items", "rows", "links"):
        out[k] = json.loads(o[k])
    return out


def _links(v):
    if not isinstance(v, list) or len(v) > 8:
        raise ApiError("At most 8 button links.")
    out = []
    for l in v:
        if not isinstance(l, dict) or l.get("type") not in LINK_TYPES:
            raise ApiError("Link type must be one of: " + ", ".join(LINK_TYPES))
        label = _str(l, "label", 100, False, "Link label")
        if l["type"] == "jml":
            addr = _jid(l.get("address"), "Link target")
        else:
            addr = _str(l, "address", 500, True, "Link address")
            if l["type"] == "url" and not re.match(r"^(https?|ftp|mailto):", addr, re.I):
                raise ApiError("Web links must start with http://, https://, ftp: or mailto:")
            if l["type"] in ("phone", "sms") and not re.match(r"^\+\d", addr):
                raise ApiError("Phone numbers must start with + and the country code, e.g. +353 1 234 5678.")
        out.append({"type": l["type"], "address": addr, "label": label})
    return out


def _object_fields(data, creating=False):
    out = {}
    if "jid" in data or creating:
        if data.get("jid") not in (None, ""):
            out["jid"] = _jid(data.get("jid"))
    if "type" in data or creating:
        if data.get("type") not in TYPES:
            raise ApiError("Type must be menu, text, title or list.")
        out["type"] = data["type"]
    if "title" in data or creating:
        out["title"] = _str(data, "title", 1000, False, "Title")
    if "body" in data:
        out["body"] = _str(data, "body", 20000, False, "Text", multiline=True)
    if "items" in data:
        items = data["items"]
        if not isinstance(items, list) or len(items) > jml.MAX_MENU_ITEMS:
            raise ApiError(f"A menu can hold at most {jml.MAX_MENU_ITEMS} links.")
        out["items"] = json.dumps([{"target": _jid(i.get("target"), "Link target"),
                                    "label": _str(i, "label", 300, False, "Link text")}
                                   for i in items if isinstance(i, dict)])
    if "rows" in data:
        rows = data["rows"]
        if not isinstance(rows, list) or len(rows) > 500:
            raise ApiError("At most 500 list rows.")
        clean = []
        for r in rows:
            if not isinstance(r, list) or len(r) > 12:
                raise ApiError("A list row can have at most 12 columns.")
            clean.append([_str({"c": c}, "c", 300, False, "List cell") for c in r])
        out["rows"] = json.dumps(clean)
    if "static" in data:
        out["static"] = 1 if data["static"] else 0
    if "compression" in data:
        if data["compression"] not in ("", "auto", "off"):
            raise ApiError("Invalid compression setting.")
        out["compression"] = data["compression"]
    if "repeat" in data:
        out["repeat"] = _int(data, "repeat", 0, 20, "Repeats")
    if "expires" in data:
        v = _str(data, "expires", 40, False, "Expiry")
        if v:
            try:
                d = datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ApiError("Expiry must be a date and time.")
            if d.tzinfo is None:
                d = d.replace(tzinfo=build.get_tz(db.get_setting("timezone")))
            v = d.isoformat()
        out["expires"] = v
    if "lifetime" in data:
        out["lifetime"] = _int(data, "lifetime", 0, 65535, "Lifetime")
    if "language" in data:
        v = _str(data, "language", 3, False, "Language").lower()
        if v and not re.fullmatch(r"[a-z]{3}", v):
            raise ApiError("Language must be a 3-letter ISO 639-2 code, e.g. eng, gle, deu.")
        out["language"] = v
    if "links" in data:
        out["links"] = json.dumps(_links(data["links"]))
    if "note" in data:
        out["note"] = _str(data, "note", 200, False, "Note")
    return out


def _insert_object(sid, f):
    now = time.time()
    f = dict(f, service_id=sid, created_at=now, updated_at=now)
    return db.x(f"INSERT INTO objects({','.join(f)}) VALUES ({','.join('?' * len(f))})", tuple(f.values())).lastrowid


def _check_size(row):
    """Encode the object once so a too-large object is refused on save."""
    try:
        jml.encode(build.object_row_to_dict(row))
    except jml.EncodeError as e:
        raise ApiError(str(e).replace(f"object 0x{row['jid']:04X} is", "This object would be")
                       + " - shorten it or split it into several objects.")


def _get_object(oid):
    o = db.q1("SELECT * FROM objects WHERE id = ?", (oid,))
    if not o:
        raise ApiError("Object not found.", 404)
    return o


def _append_link(sid, parent_jid, target, label):
    p = db.q1("SELECT * FROM objects WHERE service_id = ? AND jid = ? AND type = 'menu'", (sid, parent_jid))
    if not p:
        raise ApiError("The parent menu does not exist.")
    items = json.loads(p["items"])
    if len(items) >= jml.MAX_MENU_ITEMS:
        raise ApiError(f"That menu already has {jml.MAX_MENU_ITEMS} links - the most a menu can hold.")
    items.append({"target": target, "label": label})
    db.x("UPDATE objects SET items = ?, updated_at = ? WHERE id = ?", (json.dumps(items), time.time(), p["id"]))


@bp.post("/api/services/<int:sid>/objects")
@require("editor")
def create_object(sid):
    check_service(sid)
    data = json_body()
    f = _object_fields(data, creating=True)
    if "jid" not in f:
        f["jid"] = next_free_jid(sid)
    elif f["jid"] in build.used_ids(sid):
        raise ApiError(f"Object ID 0x{f['jid']:04X} is already used in this service.")
    defaults = {"body": "", "items": "[]", "rows": "[]", "links": "[]", "static": 0}
    row = {**defaults, **f}
    if not row["title"]:
        raise ApiError("Give it a title.")
    if row["type"] == "text" and not row["body"]:
        row["body"] = row["title"]
    if row["type"] == "list" and row["rows"] == "[]":
        row["rows"] = json.dumps([["First row", ""]])
    _check_size({**row, "compression": "", "repeat": 0, "expires": "", "lifetime": 0, "language": ""})
    with db.transaction():
        oid = _insert_object(sid, row)
        if data.get("parent") not in (None, ""):
            _append_link(sid, _jid(data["parent"], "Parent menu"), f["jid"],
                         _str(data, "label", 300, False, "Link text") or f["title"][:60])
    db.mark_dirty()
    audit("object.create", f"{sid}:0x{f['jid']:04X}", {"type": row["type"]})
    return jsonify(id=oid, jid=f["jid"])


@bp.get("/api/objects/<int:oid>")
@require()
def get_object(oid):
    o = _get_object(oid)
    out = _object_public(o)
    out["referenced_by"] = _referrers(o["service_id"], o["jid"])
    return jsonify(out)


def _referrers(sid, jid):
    out = []
    for m in db.q("SELECT jid, title, items, links FROM objects WHERE service_id = ?", (sid,)):
        if any(i["target"] == jid for i in json.loads(m["items"])) or \
                any(l["type"] == "jml" and l["address"] == jid for l in json.loads(m["links"])):
            out.append({"jid": m["jid"], "title": m["title"]})
    return out


def _retarget(sid, old, new):
    """Point every menu link and button link at `old` to `new` (None removes them)."""
    for m in db.q("SELECT id, items, links FROM objects WHERE service_id = ?", (sid,)):
        items, links = json.loads(m["items"]), json.loads(m["links"])
        ni = [dict(i, target=new) if i["target"] == old else i for i in items if not (i["target"] == old and new is None)]
        nl = [dict(l, address=new) if l["type"] == "jml" and l["address"] == old else l for l in links
              if not (l["type"] == "jml" and l["address"] == old and new is None)]
        if ni != items or nl != links:
            db.x("UPDATE objects SET items = ?, links = ?, updated_at = ? WHERE id = ?",
                 (json.dumps(ni), json.dumps(nl), time.time(), m["id"]))


def _relabel(sid, jid, old_titles, new_title):
    """Menu links whose text was the object's old title follow the new title.
    Link text someone changed on purpose is left alone."""
    olds = {t.strip() for t in old_titles if t and t.strip()}
    olds |= {t[:60].strip() for t in olds}
    if not olds or not new_title.strip():
        return 0
    n = 0
    for m in db.q("SELECT id, items FROM objects WHERE service_id = ? AND type = 'menu'", (sid,)):
        items = json.loads(m["items"])
        changed = False
        for it in items:
            if it["target"] == jid and it["label"].strip() in olds:
                it["label"] = new_title.strip()[:300]
                changed = True
                n += 1
        if changed:
            db.x("UPDATE objects SET items = ?, updated_at = ? WHERE id = ?", (json.dumps(items), time.time(), m["id"]))
    return n


@bp.post("/api/services/<int:sid>/link-text")
@require("editor")
def set_link_text(sid):
    """Change the text a menu shows for one of its links."""
    check_service(sid)
    data = json_body()
    menu_jid = _jid(data.get("menu"), "Menu")
    target = _jid(data.get("target"), "Object")
    label = _str(data, "label", 300, True, "Link text")
    m = db.q1("SELECT * FROM objects WHERE service_id = ? AND jid = ? AND type = 'menu'", (sid, menu_jid))
    if not m:
        raise ApiError("Menu not found.", 404)
    items = json.loads(m["items"])
    i = data.get("index")
    if not (isinstance(i, int) and 0 <= i < len(items) and items[i]["target"] == target):
        i = next((n for n, it in enumerate(items) if it["target"] == target), None)
    if i is None:
        raise ApiError("That menu doesn't link to the object any more - reload the page.", 409)
    items[i]["label"] = label
    db.x("UPDATE objects SET items = ?, updated_at = ? WHERE id = ?", (json.dumps(items), time.time(), m["id"]))
    db.mark_dirty()
    audit("tree.link_text", f"{sid}:0x{target:04X}", {"menu": menu_jid})
    return jsonify(ok=True)


def _menu_descendants(sid, root):
    """Every object reachable from `root` through menu links (manual menus only)."""
    menus = {m["jid"]: [i["target"] for i in json.loads(m["items"])]
             for m in db.q("SELECT jid, items FROM objects WHERE service_id = ? AND type = 'menu'", (sid,))}
    seen, todo = set(), [root]
    while todo:
        for t in menus.get(todo.pop(), []):
            if t not in seen:
                seen.add(t)
                todo.append(t)
    return seen


@bp.post("/api/services/<int:sid>/move")
@require("editor")
def move_link(sid):
    """Reorganise the tree: move (or, with copy, add) a link to `target` from
    menu `from` (at `from_index`) into menu `to` at `index`. `to` = null only
    removes the link from `from`."""
    check_service(sid)
    data = json_body()
    target = _jid(data.get("target"), "Object")
    if target not in build.used_ids(sid):
        raise ApiError("That object doesn't exist.", 404)
    src = _jid(data["from"], "Source menu") if data.get("from") not in (None, "") else None
    dst = _jid(data["to"], "Target menu") if data.get("to") not in (None, "") else None
    copy = bool(data.get("copy"))
    if src is None and dst is None:
        raise ApiError("Nothing to move.")

    def menu(jid, label):
        m = db.q1("SELECT * FROM objects WHERE service_id = ? AND jid = ?", (sid, jid))
        if not m or m["type"] != "menu":
            raise ApiError(f"The {label} isn't a menu you can edit (feed menus are filled by the feed).")
        return m, json.loads(m["items"])

    with db.transaction():
        label, removed_at = None, None
        if src is not None and not copy:
            sm, sitems = menu(src, "source")
            i = data.get("from_index")
            if not (isinstance(i, int) and 0 <= i < len(sitems) and sitems[i]["target"] == target):
                i = next((n for n, it in enumerate(sitems) if it["target"] == target), None)
            if i is None:
                raise ApiError("That menu doesn't link to the object any more - reload the page.", 409)
            label = sitems.pop(i)["label"]
            removed_at = i
            if dst != src:
                db.x("UPDATE objects SET items = ?, updated_at = ? WHERE id = ?", (json.dumps(sitems), time.time(), sm["id"]))
        if dst is not None:
            if dst == target:
                raise ApiError("A menu can't be put inside itself.")
            if target != 0 and not copy and src is not None and dst in _menu_descendants(sid, target):
                raise ApiError("That would put a menu inside one of its own sub-menus and cut it off from the root.")
            dm, ditems = (sm, sitems) if (dst == src and not copy) else menu(dst, "target")
            if any(it["target"] == target for it in ditems):
                raise ApiError("That menu already links to this object.")
            if len(ditems) >= jml.MAX_MENU_ITEMS:
                raise ApiError(f"That menu already has {jml.MAX_MENU_ITEMS} links - the most a menu can hold.")
            if label is None:
                ref = next((it["label"] for m in db.q("SELECT items FROM objects WHERE service_id = ?", (sid,))
                            for it in json.loads(m["items"]) if it["target"] == target), None)
                if ref is None:
                    o = db.q1("SELECT title FROM objects WHERE service_id = ? AND jid = ?", (sid, target)) or \
                        db.q1("SELECT COALESCE(NULLIF(title, ''), NULLIF(name, ''), 'News') AS title FROM feeds "
                              "WHERE service_id = ? AND jid = ?", (sid, target))
                    ref = (o["title"] if o else "")[:60] or hex(target)
                label = ref
            idx = data.get("index")
            if isinstance(idx, int) and dst == src and removed_at is not None and removed_at < idx:
                idx -= 1  # `index` counts the links as they were before the move
            idx = len(ditems) if not isinstance(idx, int) else max(0, min(idx, len(ditems)))
            ditems.insert(idx, {"target": target, "label": label})
            db.x("UPDATE objects SET items = ?, updated_at = ? WHERE id = ?", (json.dumps(ditems), time.time(), dm["id"]))
    db.mark_dirty()
    audit("tree.move", f"{sid}:0x{target:04X}", {"from": src, "to": dst, "copy": copy})
    return jsonify(ok=True)


@bp.put("/api/objects/<int:oid>")
@require("editor")
def update_object(oid):
    o = _get_object(oid)
    data = json_body()
    f = _object_fields(data)
    new_jid = f.get("jid", o["jid"])
    if new_jid != o["jid"]:
        if o["jid"] == 0:
            raise ApiError("The root object keeps ID 0x0000 - receivers start there.")
        if new_jid in build.used_ids(o["service_id"]):
            raise ApiError(f"Object ID 0x{new_jid:04X} is already used in this service.")
    row = {**o, **f}
    _check_size(row)
    f["updated_at"] = time.time()
    with db.transaction():
        db.x(f"UPDATE objects SET {', '.join(k + ' = ?' for k in f)} WHERE id = ?", (*f.values(), oid))
        if new_jid != o["jid"]:
            _retarget(o["service_id"], o["jid"], new_jid)
        if "title" in f and f["title"] != o["title"]:
            _relabel(o["service_id"], new_jid, [o["title"]], f["title"])
    db.mark_dirty()
    audit("object.update", f"{o['service_id']}:0x{new_jid:04X}")
    return jsonify(ok=True)


@bp.delete("/api/objects/<int:oid>")
@require("editor")
def delete_object(oid):
    o = _get_object(oid)
    if o["jid"] == 0:
        raise ApiError("The root object (0x0000) cannot be deleted - receivers start there. Edit it instead.")
    with db.transaction():
        db.x("DELETE FROM objects WHERE id = ?", (oid,))
        _retarget(o["service_id"], o["jid"], None)
    db.mark_dirty()
    audit("object.delete", f"{o['service_id']}:0x{o['jid']:04X}")
    return jsonify(ok=True)


# --- feeds --------------------------------------------------------------------------------

def _feed_public(f):
    out = {k: v for k, v in f.items() if k not in ("items", "id_map", "content_hash")}
    items = json.loads(f["items"])
    out["item_count"] = len(items)
    out["headlines"] = [i["title"] for i in items[:f["max_items"]]][:5]
    out["story_ids"] = sorted(int(v) for v in json.loads(f["id_map"]).values())
    return out


def _feed_fields(data, creating=False):
    out = {}
    if "url" in data or creating:
        out["url"] = _url(data.get("url"), "Feed URL")
    if "mode" in data or creating:
        if data.get("mode") not in ("menu", "ticker", "list"):
            raise ApiError("Mode must be menu, ticker or list.")
        out["mode"] = data["mode"]
    if "name" in data:
        out["name"] = _str(data, "name", 64, False, "Name")
    if "title" in data:
        out["title"] = _str(data, "title", 200, False, "Title")
    if "max_items" in data:
        out["max_items"] = _int(data, "max_items", 1, feeds.MAX_ITEMS, "Number of stories")
    if "item_text" in data:
        if data["item_text"] not in ("description", "title"):
            raise ApiError("Invalid story text setting.")
        out["item_text"] = data["item_text"]
    for k in ("show_time", "static", "enabled"):
        if k in data:
            out[k] = 1 if data[k] else 0
    return out


def _insert_feed(sid, f):
    now = time.time()
    f = dict(f, service_id=sid, created_at=now, updated_at=now)
    return db.x(f"INSERT INTO feeds({','.join(f)}) VALUES ({','.join('?' * len(f))})", tuple(f.values())).lastrowid


def _get_feed(fid):
    f = db.q1("SELECT * FROM feeds WHERE id = ?", (fid,))
    if not f:
        raise ApiError("Feed not found.", 404)
    return f


@bp.post("/api/services/<int:sid>/feeds")
@require("editor")
def create_feed(sid):
    check_service(sid)
    data = json_body()
    f = _feed_fields(data, creating=True)
    if data.get("jid") not in (None, ""):
        f["jid"] = _jid(data["jid"])
        if f["jid"] in build.used_ids(sid):
            raise ApiError(f"Object ID 0x{f['jid']:04X} is already used in this service.")
    else:
        f["jid"] = next_free_jid(sid)
    with db.transaction():
        fid = _insert_feed(sid, f)
        if data.get("parent") not in (None, ""):
            _append_link(sid, _jid(data["parent"], "Parent menu"), f["jid"],
                         _str(data, "label", 300, False, "Link text") or f.get("title") or f.get("name") or "News")
    err, _ = build.refresh_feed(_get_feed(fid), bool(db.get_setting("allow_private_urls")))
    db.mark_dirty()
    audit("feed.create", f["url"][:200], {"service": sid})
    return jsonify(id=fid, jid=f["jid"], error=err or None)


@bp.put("/api/feeds/<int:fid>")
@require("editor")
def update_feed(fid):
    old = _get_feed(fid)
    data = json_body()
    f = _feed_fields(data)
    if "jid" in data and _jid(data["jid"]) != old["jid"]:
        new = _jid(data["jid"])
        if new == 0:
            raise ApiError("A feed cannot be the root object.")
        if new in build.used_ids(old["service_id"]):
            raise ApiError(f"Object ID 0x{new:04X} is already used in this service.")
        f["jid"] = new
    f["updated_at"] = time.time()
    with db.transaction():
        db.x(f"UPDATE feeds SET {', '.join(k + ' = ?' for k in f)} WHERE id = ?", (*f.values(), fid))
        if "jid" in f:
            _retarget(old["service_id"], old["jid"], f["jid"])
        if "title" in f and f["title"] != old["title"]:
            _relabel(old["service_id"], f.get("jid", old["jid"]), [old["title"], old["name"]], f["title"])
    err = None
    if "url" in f or "max_items" in f or "mode" in f:
        db.x("UPDATE feeds SET content_hash = '' WHERE id = ?", (fid,))
        err, _ = build.refresh_feed(_get_feed(fid), bool(db.get_setting("allow_private_urls")))
    db.mark_dirty()
    audit("feed.update", old["url"][:200])
    return jsonify(ok=True, error=err or None)


@bp.delete("/api/feeds/<int:fid>")
@require("editor")
def delete_feed(fid):
    f = _get_feed(fid)
    with db.transaction():
        db.x("DELETE FROM feeds WHERE id = ?", (fid,))
        _retarget(f["service_id"], f["jid"], None)
    db.mark_dirty()
    audit("feed.delete", f["url"][:200])
    return jsonify(ok=True)


@bp.post("/api/feeds/<int:fid>/refresh")
@require("editor")
def refresh_feed(fid):
    f = _get_feed(fid)
    err, changed = build.refresh_feed(f, bool(db.get_setting("allow_private_urls")))
    if err:
        raise ApiError(f"Feed could not be read: {err}")
    return jsonify(ok=True, changed=changed, feed=_feed_public(_get_feed(fid)))


@bp.post("/api/feeds/test")
@require("editor")
def test_feed():
    data = json_body()
    url = _url(data.get("url"), "Feed URL")
    try:
        raw, _, _ = fetch.fetch(url, allow_private=bool(db.get_setting("allow_private_urls")),
                                max_bytes=10 * 1024 * 1024)
        parsed = feeds.parse(raw)
    except (fetch.FetchError, feeds.FeedError) as e:
        raise ApiError(f"Feed could not be read: {e}")
    return jsonify(title=parsed["title"], count=len(parsed["items"]),
                   items=[{"title": i["title"], "text": i["text"][:300], "published": i["published"]}
                          for i in parsed["items"][:10]])


# --- users --------------------------------------------------------------------------------

def _user_row(u):
    out = {k: u[k] for k in ("id", "username", "display_name", "role", "disabled", "must_change_pw", "created_at",
                             "last_login")}
    out["locked"] = u["locked_until"] > time.time()
    return out


@bp.get("/api/users")
@require("admin")
def list_users():
    return jsonify([_user_row(u) for u in db.q("SELECT * FROM users ORDER BY username COLLATE NOCASE")])


def _user_fields(data, creating):
    out = {}
    if "display_name" in data:
        out["display_name"] = _str(data, "display_name", 64)
    if "role" in data or creating:
        if data.get("role") not in ("admin", "editor"):
            raise ApiError("Role must be admin or editor.")
        out["role"] = data["role"]
    if "disabled" in data:
        out["disabled"] = 1 if data["disabled"] else 0
    return out


@bp.post("/api/users")
@require("admin")
def create_user():
    data = json_body()
    username = _str(data, "username", 64, True, "Username")
    if not USERNAME_RE.match(username):
        raise ApiError("Username may contain letters, digits and . _ @ - (3-64 characters).")
    if db.q1("SELECT id FROM users WHERE username = ?", (username,)):
        raise ApiError("That username is taken.")
    pw = data.get("password") or ""
    generated = not pw
    if generated:
        pw = secrets.token_urlsafe(12)
    problem = security.password_problem(pw, username)
    if problem:
        raise ApiError(problem)
    f = _user_fields(data, True)
    f.update(username=username, pw_hash=security.hash_password(pw), created_at=time.time(), must_change_pw=1)
    uid = db.x(f"INSERT INTO users({','.join(f)}) VALUES ({','.join('?' * len(f))})", tuple(f.values())).lastrowid
    audit("user.create", username, {"role": f["role"]})
    return jsonify(id=uid, password=pw if generated else None)


@bp.patch("/api/users/<int:uid>")
@require("admin")
def update_user(uid):
    u = db.q1("SELECT * FROM users WHERE id = ?", (uid,))
    if not u:
        raise ApiError("User not found.", 404)
    data = json_body()
    f = _user_fields(data, False)
    if uid == current_user()["id"] and (f.get("role", "admin") != "admin" or f.get("disabled")):
        raise ApiError("You cannot demote or disable your own account.")
    if u["role"] == "admin" and (f.get("role", "admin") != "admin" or f.get("disabled")):
        if db.q1("SELECT COUNT(*) AS n FROM users WHERE role = 'admin' AND disabled = 0")["n"] <= 1:
            raise ApiError("At least one active administrator is required.")
    if f:
        db.x(f"UPDATE users SET {', '.join(k + ' = ?' for k in f)} WHERE id = ?", (*f.values(), uid))
    if data.get("unlock"):
        db.x("UPDATE users SET locked_until = 0, failed_logins = 0 WHERE id = ?", (uid,))
    if f.get("disabled") or ("role" in f and f["role"] != u["role"]):
        security.destroy_user_sessions(uid)
    audit("user.update", u["username"], f)
    return jsonify(ok=True)


@bp.post("/api/users/<int:uid>/reset-password")
@require("admin")
def reset_password(uid):
    u = db.q1("SELECT * FROM users WHERE id = ?", (uid,))
    if not u:
        raise ApiError("User not found.", 404)
    pw = secrets.token_urlsafe(12)
    db.x("UPDATE users SET pw_hash = ?, must_change_pw = 1, failed_logins = 0, locked_until = 0 WHERE id = ?",
         (security.hash_password(pw), uid))
    security.destroy_user_sessions(uid)
    audit("user.reset_password", u["username"])
    return jsonify(password=pw)


@bp.delete("/api/users/<int:uid>")
@require("admin")
def delete_user(uid):
    if uid == current_user()["id"]:
        raise ApiError("You cannot delete your own account.")
    u = db.q1("SELECT * FROM users WHERE id = ?", (uid,))
    if not u:
        raise ApiError("User not found.", 404)
    if u["role"] == "admin" and db.q1("SELECT COUNT(*) AS n FROM users WHERE role='admin'")["n"] <= 1:
        raise ApiError("At least one administrator is required.")
    db.x("DELETE FROM users WHERE id = ?", (uid,))
    audit("user.delete", u["username"])
    return jsonify(ok=True)


# --- settings -----------------------------------------------------------------------------

SETTING_KEYS = ("mux_name", "ensemble", "mux_services", "refresh_minutes", "timezone", "allow_private_urls", "session_hours",
                "setup_complete")


@bp.get("/api/settings")
@require()
def get_settings():
    s = db.all_settings()
    keys = SETTING_KEYS if current_user()["role"] == "admin" else ("mux_name", "ensemble", "mux_services", "timezone")
    return jsonify({k: s[k] for k in keys})


@bp.put("/api/settings")
@require("admin")
def put_settings():
    data = json_body()
    out = {}
    if "mux_name" in data:
        out["mux_name"] = _str(data, "mux_name", 64, False, "Multiplex name")
    if "ensemble" in data:
        if not isinstance(data["ensemble"], dict):
            raise ApiError("Invalid ensemble.")
        out["ensemble"] = _ensemble(data["ensemble"])
    if "refresh_minutes" in data:
        out["refresh_minutes"] = _int(data, "refresh_minutes", 5, 1440, "Refresh interval")
    if "timezone" in data:
        tzn = _str(data, "timezone", 64)
        if not build.valid_tz(tzn):
            raise ApiError("Unknown timezone (use e.g. Europe/Dublin).")
        out["timezone"] = tzn
    for k in ("allow_private_urls", "setup_complete"):
        if k in data:
            out[k] = bool(data[k])
    if "session_hours" in data:
        out["session_hours"] = _int(data, "session_hours", 1, 168, "Session length")
    for k, v in out.items():
        db.set_setting(k, v)
    if "timezone" in out:
        db.mark_dirty()
    scheduler.wake()
    audit("settings.update", "", out)
    return jsonify(ok=True)


# --- file browser (admin only) ------------------------------------------------------------

@bp.get("/api/fs")
@require("admin")
def fs_list():
    path = request.args.get("path") or "/"
    if not os.path.isabs(path) or "\x00" in path:
        raise ApiError("Path must be absolute.")
    path = os.path.realpath(path)
    if not os.path.isdir(path):
        raise ApiError("Not a directory.", 404)
    exts = tuple("." + e.strip().lower() for e in request.args.get("files", "").split(",") if e.strip())
    entries = []
    try:
        with os.scandir(path) as it:
            for e in it:
                if e.name.startswith(".") and request.args.get("hidden") != "1":
                    continue
                try:
                    st = e.stat(follow_symlinks=True)
                except OSError:
                    continue
                if stat.S_ISDIR(st.st_mode):
                    entries.append({"name": e.name, "dir": True})
                elif exts and stat.S_ISREG(st.st_mode) and e.name.lower().endswith(exts):
                    entries.append({"name": e.name, "dir": False, "size": st.st_size, "mtime": st.st_mtime})
                if len(entries) >= 2000:
                    break
    except PermissionError:
        raise ApiError("Permission denied for the service user.", 403)
    entries.sort(key=lambda x: (not x["dir"], x["name"].lower()))
    return jsonify(path=path, parent=os.path.dirname(path) if path != "/" else None,
                   writable=os.access(path, os.W_OK), entries=entries)


@bp.post("/api/fs/mkdir")
@require("admin")
def fs_mkdir():
    data = json_body()
    parent = os.path.realpath(_str(data, "path", 1024, True))
    name = _str(data, "name", 128, True, "Folder name")
    if not os.path.isabs(parent) or not re.fullmatch(r"[A-Za-z0-9._ -]+", name) or name in (".", ".."):
        raise ApiError("Invalid folder name.")
    target = os.path.join(parent, name)
    try:
        os.mkdir(target, 0o755)
    except FileExistsError:
        raise ApiError("Folder already exists.")
    except OSError as e:
        raise ApiError(f"Could not create folder: {e.strerror}")
    audit("fs.mkdir", target)
    return jsonify(path=target)


# --- one-click update (admin) -------------------------------------------------------------

def _update_paths():
    cfg = current_app.config["ODR_CFG"]
    return {
        "request": os.path.join(cfg["data_dir"], "update-request"),
        "status": cfg.get("update_status", "/var/lib/odr-journaline-encoder-update/status.json"),
        "conf": cfg.get("update_conf", "/etc/odr-journaline-encoder/update.conf"),
        "commit": cfg.get("installed_commit", "/opt/odr-journaline-encoder/COMMIT"),
    }


def _read_small(path, limit=65536):
    try:
        with open(path, "rb") as f:
            return f.read(limit).decode("utf-8", "replace")
    except OSError:
        return None


def _update_info():
    paths = _update_paths()
    conf = {}
    for line in (_read_small(paths["conf"]) or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            conf[k.strip()] = v.strip()
    status_ = {}
    try:
        status_ = json.loads(_read_small(paths["status"]) or "{}")
    except ValueError:
        pass
    source = re.sub(r"(://)[^/@]*@", r"\1", conf.get("REPO_URL", ""), count=1)  # hide embedded credentials
    return {
        "enabled": bool(conf.get("REPO_URL") and conf.get("BRANCH")),
        "version": __version__,
        "current_commit": (_read_small(paths["commit"]) or "").strip(),
        "source": source, "branch": conf.get("BRANCH", ""),
        "status": status_ if isinstance(status_, dict) else {},
        "pending": os.path.exists(paths["request"]),
    }


@bp.get("/api/update")
@require("admin")
def update_info():
    return jsonify(_update_info())


@bp.post("/api/update")
@require("admin")
def request_update():
    action = json_body().get("action")
    if action not in ("check", "apply"):
        raise ApiError("Action must be check or apply.")
    info = _update_info()
    if not info["enabled"]:
        raise ApiError("Updates are not configured - reinstall from a git checkout with install.sh.")
    if info["status"].get("state") == "running" or info["pending"]:
        raise ApiError("An update task is already running.", 409)
    fd = os.open(_update_paths()["request"], os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o640)
    with os.fdopen(fd, "w") as f:
        f.write(action)
    audit("update." + action)
    return jsonify(ok=True)


# --- audit --------------------------------------------------------------------------------

@bp.get("/api/audit")
@require("admin")
def audit_log():
    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        offset = 0
    rows = db.q("SELECT * FROM audit ORDER BY id DESC LIMIT 100 OFFSET ?", (offset,))
    for r in rows:
        r["details"] = json.loads(r["details"])
    return jsonify(rows)
