"""JML decoder, used for the receiver preview in the web UI and for tests.

It is written independently from the encoder, straight from the spec text,
so a round trip through both checks the encoder."""

import zlib

from . import jml

TEXT_STOP = {jml.C_END, jml.C_TITLE, jml.C_LINK, jml.C_BODY, jml.C_ITEM, jml.C_COLUMN}


class DecodeError(ValueError):
    pass


def _text(buf, pos, extras):
    """Read text up to the next JML code. Returns (segments, pos).

    segments is a list of (kind, value): ("t", str), ("br",), ("hl", bool),
    ("intro",), ("wb",). Data sections are decoded into `extras`."""
    segs, raw = [], bytearray()

    def flush():
        if raw:
            segs.append(("t", raw.decode("utf-8", "replace")))
            raw.clear()

    while pos < len(buf):
        c = buf[pos]
        if c in TEXT_STOP:
            break
        if c >= 0x20:
            raw.append(c)
            pos += 1
            continue
        flush()
        if c == jml.E_LINE_BREAK:
            segs.append(("br",))
        elif c == jml.E_WORD_BREAK:
            segs.append(("wb",))
        elif c == jml.E_HIGHLIGHT_START:
            segs.append(("hl", True))
        elif c == jml.E_HIGHLIGHT_STOP:
            segs.append(("hl", False))
        elif c == jml.E_END_OF_INTRO:
            segs.append(("intro",))
        elif c in (jml.E_DS_START, jml.E_DS_CONT):
            if c == jml.E_DS_CONT:
                raise DecodeError("data section continuation without a start")
            payload = bytearray()
            while True:
                if pos + 1 >= len(buf):
                    raise DecodeError("truncated data section")
                n = buf[pos + 1] + 1
                chunk = buf[pos + 2:pos + 2 + n]
                if len(chunk) != n:
                    raise DecodeError("truncated data section")
                payload += chunk
                pos += 2 + n
                if n == 256 and pos < len(buf) and buf[pos] == jml.E_DS_CONT:
                    continue
                break
            extras.append(_data_section(bytes(payload)))
            continue
        elif c in (jml.E_EXT_BEGIN, jml.E_EXT_END):
            pos += 2
            continue
        pos += 1
    flush()
    return segs, pos


def _data_section(p):
    t, d = p[0], p[1:]
    if t == jml.DS_ABS_TIMEOUT and len(d) == 3:
        from datetime import timedelta
        return {"ds": "expires", "value": (jml.EPOCH + timedelta(minutes=15 * int.from_bytes(d, "big"))).isoformat()}
    if t == jml.DS_REL_TIMEOUT and len(d) == 2:
        return {"ds": "lifetime", "value": int.from_bytes(d, "big")}
    if t == jml.DS_LANGUAGE:
        return {"ds": "language", "value": d.decode("ascii", "replace")}
    if t == jml.DS_LINK and d:
        lt = d[0]
        rest = d[1:]
        if lt == jml.LINK_JML:
            addr, label = int.from_bytes(rest[:2], "big"), rest[3:] if len(rest) > 2 else b""
        else:
            addr, _, label = rest.partition(b"\x00")
            addr = addr.decode("utf-8", "replace")
        return {"ds": "link", "type": jml.LINK_TYPE_NAMES.get(lt, lt), "address": addr,
                "label": bytes(label).decode("utf-8", "replace")}
    if t == jml.DS_POSITIONS:
        pts = []
        for i in range(0, len(d) - 5, 6):
            la = int.from_bytes(d[i:i + 3], "big", signed=True)
            lo = int.from_bytes(d[i + 3:i + 6], "big", signed=True)
            pts.append((la / 92000, lo / 46000))
        return {"ds": "positions", "value": pts}
    return {"ds": "other", "type": t, "length": len(d)}


def plain(segs):
    """Segments as plain text (line breaks as \\n, other codes dropped)."""
    out = []
    for s in segs:
        if s[0] == "t":
            out.append(s[1])
        elif s[0] == "br":
            out.append("\n")
    return "".join(out)


def decode(obj, ext_header_len=0):
    """Decode an encoded JML object into a dict (see jml.content for the shape),
    with each text also given as segments for rich rendering."""
    if len(obj) < 4:
        raise DecodeError("object too short")
    oid = int.from_bytes(obj[:2], "big")
    desc = obj[2]
    otype = desc >> 5
    if otype not in jml.TYPE_NAMES:
        raise DecodeError(f"unknown object type {otype}")
    compressed = bool(desc & 0x08)
    buf = obj[3 + ext_header_len:]
    if compressed:
        if buf[0] != jml.COMPRESSION_DEFLATE:
            raise DecodeError(f"unknown compression method 0x{buf[0]:02x}")
        try:
            buf = zlib.decompress(buf[1:], -15)
        except zlib.error as e:
            raise DecodeError(f"deflate error: {e}")
    extras = []
    pos = 0
    # data sections may come before the title code
    pre, pos = _text(buf, pos, extras)
    if pos >= len(buf) or buf[pos] != jml.C_TITLE:
        raise DecodeError("content must start with a title block")
    title, pos = _text(buf, pos + 1, extras)
    out = {"id": oid, "type": jml.TYPE_NAMES[otype], "static": bool(desc & 0x10), "compressed": compressed,
           "revision": desc & 7, "title": plain(title), "title_segs": title, "size": len(obj),
           "content_size": len(buf)}
    items, rows, body = [], [], None
    while pos < len(buf):
        code = buf[pos]
        pos += 1
        if code == jml.C_END:
            continue
        if code == jml.C_LINK:
            if pos + 2 > len(buf):
                raise DecodeError("truncated link item")
            target = int.from_bytes(buf[pos:pos + 2], "big")
            segs, pos = _text(buf, pos + 2, extras)
            items.append({"target": target, "label": plain(segs), "segs": segs})
        elif code == jml.C_BODY:
            body, pos = _text(buf, pos, extras)
        elif code == jml.C_ITEM:
            row = []
            segs, pos = _text(buf, pos, extras)
            row.append(plain(segs))
            while pos < len(buf) and buf[pos] == jml.C_COLUMN:
                segs, pos = _text(buf, pos + 1, extras)
                row.append(plain(segs))
            rows.append(row)
        else:
            segs, pos = _text(buf, pos, extras)  # unknown code: keep its content
    if out["type"] == "menu":
        out["items"] = items
    elif out["type"] == "text":
        out["body"] = plain(body or [])
        out["body_segs"] = body or []
    elif out["type"] == "list":
        out["rows"] = rows
    for e in extras:
        if e["ds"] == "link":
            out.setdefault("links", []).append({k: e[k] for k in ("type", "address", "label")})
        elif e["ds"] in ("expires", "lifetime", "language", "positions"):
            out[e["ds"]] = e["value"]
    return out
