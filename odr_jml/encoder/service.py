"""A whole Journaline service: validation, revision tracking, TOC and the
weighted carousel (ETSI TS 102 979 clauses 4.3, 5, 6 and 8.1)."""

import hashlib
import json
from collections import deque

from . import jml, msc, toc

DEFAULT_WEIGHTS = {"menu": 4, "title": 4, "list": 2, "text": 1, "toc": 2, "root_bonus": 2}


# --- validation --------------------------------------------------------------------------

def _visible(s):
    return bool(jml.visible_length(jml.text_bytes(s or "", markup=True)))


def validate(objects):
    """Check a service's objects against the spec's hard rules.

    Returns (errors, warnings): lists of (object_id or None, message)."""
    errors, warnings = [], []
    ids = {}
    for o in objects:
        oid = o["id"]
        if oid in ids:
            errors.append((oid, f"object ID 0x{oid:04X} is used twice"))
        ids[oid] = o
        if not 0 <= oid <= jml.MAX_FREE_ID:
            errors.append((oid, f"object ID 0x{oid:04X} is outside 0x0000-0xEFFF"))
        if not _visible(o.get("title")):
            errors.append((oid, "title is empty"))
        t = o["type"]
        if t == "menu":
            items = o.get("items") or []
            if not items:
                errors.append((oid, "a menu needs at least one link"))
            if len(items) > jml.MAX_MENU_ITEMS:
                errors.append((oid, f"a menu can hold at most {jml.MAX_MENU_ITEMS} links ({len(items)} given)"))
            for it in items:
                if not _visible(it.get("label")):
                    errors.append((oid, "a menu link has no text"))
        elif t == "text":
            if not _visible(o.get("body")):
                errors.append((oid, "the message text is empty"))
        elif t == "list":
            rows = o.get("rows") or []
            if not rows:
                errors.append((oid, "a list needs at least one row"))
            for r in rows:
                if not any(_visible(c) for c in r):
                    errors.append((oid, "a list row is empty"))
                    break
            ncols = max((len(r) for r in rows), default=0)
            for c in range(ncols):
                if not any(c < len(r) and _visible(r[c]) for r in rows):
                    warnings.append((oid, f"list column {c + 1} is empty in every row"))
        elif t != "title":
            errors.append((oid, f"unknown type {t}"))

    if 0 not in ids:
        errors.append((None, "there is no root object (ID 0x0000) - receivers start there"))
    for o in objects:
        for it in (o.get("items") or []) if o["type"] == "menu" else []:
            if it["target"] not in ids:
                errors.append((o["id"], f"links to object 0x{it['target']:04X}, which does not exist"))
        for l in o.get("links") or []:
            if l.get("type") == "jml" and int(l["address"]) not in ids:
                errors.append((o["id"], f"button link to object 0x{int(l['address']):04X}, which does not exist"))

    depth = hierarchy(objects)
    for o in objects:
        d = depth.get(o["id"])
        if d is None and o["id"] != 0:
            warnings.append((o["id"], "not reachable from the root menu"))
        elif d is not None and d > jml.MAX_HIERARCHY:
            errors.append((o["id"], f"is {d} levels deep; the limit is {jml.MAX_HIERARCHY}"))
    return errors, warnings


def hierarchy(objects):
    """Hierarchy level of each object reachable from the root (root = 1)."""
    by_id = {o["id"]: o for o in objects}
    depth = {}
    if 0 not in by_id:
        return depth
    q = deque([(0, 1)])
    depth[0] = 1
    while q:
        oid, d = q.popleft()
        o = by_id[oid]
        targets = [it["target"] for it in o.get("items") or []] if o["type"] == "menu" else []
        targets += [int(l["address"]) for l in o.get("links") or [] if l.get("type") == "jml"]
        for t in targets:
            if t in by_id and t not in depth:
                depth[t] = d + 1
                q.append((t, d + 1))
    return depth


# --- revisions ---------------------------------------------------------------------------

def content_hash(obj):
    """Hash of everything that is broadcast except the revision index."""
    c = jml.content(obj)
    return hashlib.sha1(bytes([1 if obj.get("static") else 0]) + jml.TYPE_CODES[obj["type"]].to_bytes(1, "big")
                        + c).hexdigest()


def next_revisions(objects, previous):
    """previous: {str(id): {"hash": h, "rev": r}} from the last build.
    Returns the new map; an object's revision index goes up (mod 8) only when
    its content changed. The TOC revision (key "toc") goes up (mod 256)
    whenever any object was added, removed or changed."""
    out, changed = {}, False
    for o in objects:
        key = str(o["id"])
        h = content_hash(o)
        old = previous.get(key)
        if old is None:
            out[key] = {"hash": h, "rev": 0}
            changed = True
        elif old["hash"] != h:
            out[key] = {"hash": h, "rev": (old["rev"] + 1) % 8}
            changed = True
        else:
            out[key] = old
    if set(previous) - {"toc"} - set(out):
        changed = True
    toc_old = previous.get("toc", {"rev": -1, "hash": ""})
    out["toc"] = {"rev": (toc_old["rev"] + 1) % 256 if changed or toc_old["rev"] < 0 else toc_old["rev"], "hash": ""}
    return out


# --- carousel ----------------------------------------------------------------------------

def schedule(entries):
    """entries: [(key, weight)]. Each key appears `weight` times per cycle,
    spread as evenly as possible (smooth weighted round-robin)."""
    keys = [k for k, _ in entries]
    weights = [max(1, int(w)) for _, w in entries]
    total = sum(weights)
    current = [0] * len(keys)
    order = []
    for _ in range(total):
        best = 0
        for i, w in enumerate(weights):
            current[i] += w
            if current[i] > current[best]:
                best = i
        current[best] -= total
        order.append(keys[best])
    return order


def build(objects, *, revisions=None, weights=None, toc_enabled=True, toc_timeout=0, compression="auto"):
    """Encode a service. Returns a dict with the carousel data groups, the
    encoded objects, the new revision map and statistics. Raises
    jml.EncodeError if an object is too large."""
    w = dict(DEFAULT_WEIGHTS)
    w.update(weights or {})
    revs = next_revisions(objects, revisions or {})
    encoded = {}
    for o in objects:
        mode = o.get("compression") or compression
        encoded[o["id"]] = jml.encode(o, revs[str(o["id"])]["rev"], mode)

    payloads = {}
    entries = []
    for o in sorted(objects, key=lambda x: x["id"]):
        key = ("obj", o["id"])
        payloads[key] = (msc.DG_JML, encoded[o["id"]])
        weight = o.get("repeat") or w.get(o["type"], 1)
        if o["id"] == 0:
            weight += w.get("root_bonus", 0)
        entries.append((key, weight))
    toc_blocks = []
    if toc_enabled and objects:
        toc_blocks = toc.toc_blocks([(i, jml.descriptor(b)) for i, b in encoded.items()],
                                    revs["toc"]["rev"], toc_timeout)
        for n, b in enumerate(toc_blocks):
            key = ("toc", n)
            payloads[key] = (msc.DG_MANAGEMENT, b)
            entries.append((key, w.get("toc", 1)))

    order = schedule(entries)
    groups = []
    for n, key in enumerate(order):
        dg_type, payload = payloads[key]
        groups.append(msc.datagroup(payload, dg_type, continuity=n % 16))

    per_object = []
    for o in objects:
        b = encoded[o["id"]]
        per_object.append({"id": o["id"], "type": o["type"], "bytes": len(b), "compressed": bool(b[2] & 0x08),
                           "revision": b[2] & 7, "repeats": dict(entries).get(("obj", o["id"]), 1),
                           "plain_bytes": 3 + len(jml.content(o))})
    return {
        "groups": groups, "encoded": encoded, "revisions": revs, "toc_blocks": toc_blocks,
        "objects": per_object, "order": order,
        "stats": {"objects": len(objects), "datagroups": len(groups),
                  "payload_bytes": sum(len(b) for b in encoded.values()),
                  "toc_bytes": sum(len(b) for b in toc_blocks),
                  "group_bytes": sum(len(g) for g in groups),
                  "toc_revision": revs["toc"]["rev"]},
    }


def stream(groups, bitrate, address, datagroup_mode=False):
    if datagroup_mode:
        return b"".join(groups)
    return b"".join(msc.encode_packets(groups, address=address, size=msc.packet_size_for(bitrate)))


def stable_json(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"))
