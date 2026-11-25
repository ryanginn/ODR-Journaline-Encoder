"""JML objects (ETSI TS 102 979 clause 5).

A JML object is a 3-byte standard header (object ID, object description),
an optional extended header (always 0 bytes here: ODR-DabMux signals an
extended header length of 0 in FIG 0/13), and the content section. The
content section may be deflate-compressed, in which case a compression
method byte (0x08) precedes it.
"""

import re
import zlib
from datetime import datetime, timezone

# object types (5.2)
MENU, PLAIN, TITLE, LIST = 1, 2, 3, 4
TYPE_NAMES = {MENU: "menu", PLAIN: "text", TITLE: "title", LIST: "list"}
TYPE_CODES = {v: k for k, v in TYPE_NAMES.items()}

# JML codes (table 1)
C_END, C_TITLE, C_LINK, C_BODY, C_ITEM, C_COLUMN = 0x00, 0x01, 0x02, 0x03, 0x04, 0x05

# escape sequence codes (table 2)
E_LINE_BREAK = 0x10
E_WORD_BREAK = 0x11
E_HIGHLIGHT_START = 0x12
E_HIGHLIGHT_STOP = 0x13
E_END_OF_INTRO = 0x14
E_DS_START = 0x1A
E_DS_CONT = 0x1B
E_EXT_BEGIN = 0x1C
E_EXT_END = 0x1D

# data section types (table 4)
DS_PADDING = 0x00
DS_ABS_TIMEOUT = 0x01
DS_REL_TIMEOUT = 0x02
DS_LINK = 0x03
DS_PROPRIETARY = 0xFF
DS_KEYWORD = 0x20
DS_MACRO_DEF = 0x21
DS_MACRO_REF = 0x22
DS_LANGUAGE = 0xA0
DS_LANGUAGE_SECTION = 0xA1
DS_PHONEME = 0xA2
DS_SPEECH_BREAK = 0xA3
DS_SPEECH_CHARS = 0xA4
DS_POSITIONS = 0xB0
DS_REGIONS = 0xB1

# general link types (table 5)
LINK_JML, LINK_DAB_URI, LINK_URL, LINK_PHONE, LINK_SMS = 0, 1, 2, 3, 4
LINK_TYPE_NAMES = {LINK_JML: "jml", LINK_DAB_URI: "dab", LINK_URL: "url", LINK_PHONE: "phone", LINK_SMS: "sms"}
LINK_TYPE_CODES = {v: k for k, v in LINK_TYPE_NAMES.items()}

COMPRESSION_DEFLATE = 0x08

MAX_OBJECT_SIZE = 4092
MAX_MENU_ITEMS = 32
MAX_HIERARCHY = 20
ROOT_ID = 0x0000
MAX_FREE_ID = 0xEFFF

EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)


class EncodeError(ValueError):
    pass


# --- text --------------------------------------------------------------------------------

_HIGHLIGHT = re.compile(r"\*\*(.+?)\*\*", re.S)
_INTRO = re.compile(r"^[ \t]*-{3,}[ \t]*$", re.M)


def text_bytes(s, markup=True):
    """UTF-8 text with the editor's light markup turned into escape codes:

      newline            -> 0x10 preferred line break
      **bold**           -> 0x12 ... 0x13 highlight
      a line of ---      -> 0x14 end of introductory section
      soft hyphen U+00AD -> 0x11 preferred word break

    Any other control character is dropped, so text can never be mistaken
    for a JML code or escape sequence."""
    s = (s or "").replace("\r\n", "\n").replace("\r", "\n")
    out = bytearray()
    if not markup:
        s = s.replace("\n", " ")
        return _plain(s)
    s = _INTRO.sub("\x14", s)
    pos = 0
    for m in _HIGHLIGHT.finditer(s):
        out += _plain_with_breaks(s[pos:m.start()])
        out.append(E_HIGHLIGHT_START)
        out += _plain_with_breaks(m.group(1))
        out.append(E_HIGHLIGHT_STOP)
        pos = m.end()
    out += _plain_with_breaks(s[pos:])
    return bytes(out)


def _plain_with_breaks(s):
    out = bytearray()
    for ch in s:
        if ch == "\n":
            out.append(E_LINE_BREAK)
        elif ch == "\x14":
            out.append(E_END_OF_INTRO)
        elif ch == "­":
            out.append(E_WORD_BREAK)
        elif ord(ch) >= 0x20 and ch != "\x7f":
            out += ch.encode("utf-8")
    # tidy: a line break straight after the intro marker is redundant
    return bytes(out).replace(bytes([E_END_OF_INTRO, E_LINE_BREAK]), bytes([E_END_OF_INTRO])) \
        .replace(bytes([E_LINE_BREAK, E_END_OF_INTRO]), bytes([E_END_OF_INTRO]))


def _plain(s):
    return "".join(ch for ch in s if ord(ch) >= 0x20 and ch not in "\x7f­").encode("utf-8")


def visible_length(b):
    """Number of visible characters in encoded text (escape sequences excluded)."""
    n, i = 0, 0
    while i < len(b):
        c = b[i]
        if c in (E_DS_START, E_DS_CONT):
            i += 2 + b[i + 1] + 1 if i + 1 < len(b) else 1
            continue
        if c in (E_EXT_BEGIN, E_EXT_END):
            i += 2
            continue
        if c < 0x20:
            i += 1
            continue
        if c & 0xC0 != 0x80:
            n += 1
        i += 1
    return n


# --- data sections (5.3.2.2) ------------------------------------------------------------

def data_section(ds_type, data=b""):
    """Escape sequence(s) carrying a DS payload; payloads over 256 bytes are
    split into 'data section continuation' blocks of exactly 256 bytes."""
    payload = bytes([ds_type]) + bytes(data)
    out = bytearray()
    for i in range(0, len(payload), 256):
        chunk = payload[i:i + 256]
        out += bytes([E_DS_START if i == 0 else E_DS_CONT, len(chunk) - 1]) + chunk
    return bytes(out)


def ds_absolute_timeout(when):
    """Expiry as the number of 15-minute steps since 2000-01-01 00:00 UTC (24 bits)."""
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    steps = int((when - EPOCH).total_seconds() // 900)
    if not 0 <= steps < (1 << 24):
        raise EncodeError("absolute timeout out of range")
    return data_section(DS_ABS_TIMEOUT, steps.to_bytes(3, "big"))


def ds_relative_timeout(minutes):
    minutes = int(minutes)
    if not 1 <= minutes <= 0xFFFF:
        raise EncodeError("relative timeout must be 1-65535 minutes")
    return data_section(DS_REL_TIMEOUT, minutes.to_bytes(2, "big"))


def ds_link(link_type, address, label=""):
    if isinstance(link_type, str):
        link_type = LINK_TYPE_CODES[link_type]
    if link_type == LINK_JML:
        addr = int(address).to_bytes(2, "big")
    else:
        addr = _plain(str(address))
        if not addr or b"\x00" in addr:
            raise EncodeError("link address must not be empty")
    lab = text_bytes(label, markup=False) if label else b""
    return data_section(DS_LINK, bytes([link_type]) + addr + ((b"\x00" + lab) if lab else b""))


def ds_language(code):
    code = (code or "").strip().lower()
    if not re.fullmatch(r"[a-z]{3}", code):
        raise EncodeError("language must be a 3-letter ISO 639-2 code, e.g. eng")
    return data_section(DS_LANGUAGE, code.encode("ascii"))


def ds_positions(points):
    """[(lat, lon), ...] in degrees: lat in 1/92000 deg, lon in 1/46000 deg, 24-bit two's complement."""
    if not points:
        raise EncodeError("at least one position is required")
    out = bytearray()
    for lat, lon in points:
        lat, lon = float(lat), float(lon)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise EncodeError("position out of range")
        out += (round(lat * 92000) & 0xFFFFFF).to_bytes(3, "big")
        out += (round(lon * 46000) & 0xFFFFFF).to_bytes(3, "big")
    return data_section(DS_POSITIONS, bytes(out))


# --- objects ----------------------------------------------------------------------------

def header(object_id, obj_type, static=False, compressed=False, revision=0):
    if not 0 <= object_id <= 0xFFFF:
        raise EncodeError("object id out of range")
    desc = ((obj_type & 7) << 5) | (0x10 if static else 0) | (0x08 if compressed else 0) | (revision & 7)
    return object_id.to_bytes(2, "big") + bytes([desc])


def preamble(obj):
    """Data sections that belong before the first visible character."""
    out = bytearray()
    if obj.get("expires"):
        when = obj["expires"]
        if isinstance(when, str):
            when = datetime.fromisoformat(when.replace("Z", "+00:00"))
        out += ds_absolute_timeout(when)
    if obj.get("lifetime"):
        out += ds_relative_timeout(obj["lifetime"])
    if obj.get("language"):
        out += ds_language(obj["language"])
    if obj.get("positions"):
        out += ds_positions(obj["positions"])
    for link in obj.get("links") or []:
        out += ds_link(link["type"], link["address"], link.get("label", ""))
    return bytes(out)


def content(obj):
    """Uncompressed content section for an object dict:
      type: "menu" | "text" | "title" | "list"
      title: str
      items: menu -> [{"target": int, "label": str}]
      body:  text -> str
      rows:  list -> [[col, col, ...], ...]
      expires / lifetime / language / positions / links: optional extras
    """
    t = obj["type"]
    title = text_bytes(obj.get("title", ""), markup=False)
    out = bytearray([C_TITLE]) + preamble(obj) + title
    last_item = None
    if t in ("menu", MENU):
        for it in obj.get("items") or []:
            out += bytes([C_LINK]) + int(it["target"]).to_bytes(2, "big") + text_bytes(it["label"], markup=False)
    elif t in ("text", PLAIN):
        out += bytes([C_BODY]) + text_bytes(obj.get("body", ""))
    elif t in ("list", LIST):
        for row in obj.get("rows") or []:
            cols = [text_bytes(c, markup=False) for c in row]
            # trailing empty columns carry nothing (5.3.1: missing columns are empty)
            while len(cols) > 1 and not cols[-1]:
                cols.pop()
            last_item = len(out)
            out += bytes([C_ITEM]) + bytes([C_COLUMN]).join(cols)
    elif t not in ("title", TITLE):
        raise EncodeError(f"unknown object type {t!r}")
    if last_item is not None and len(out) - last_item <= 3:
        # The widely used Fraunhofer decoder stops reading items when 3 bytes
        # or fewer are left, so a very short last list row ("x") would be lost.
        # A padding data section (ignored by every receiver) keeps it intact.
        out += data_section(DS_PADDING)
    return bytes(out)


def deflate(data):
    """Raw deflate (RFC 1951) with a 4 096-byte window, as clause 5.2 requires."""
    c = zlib.compressobj(9, zlib.DEFLATED, -12, 9)
    return c.compress(data) + c.flush()


def encode(obj, revision=0, compression="auto"):
    """Encode one JML object. Returns bytes; raises EncodeError if it is too large.

    compression: "auto" (only when smaller), "on" (when smaller - the spec
    forbids sending a larger compressed object) or "off"."""
    t = obj["type"]
    code = t if isinstance(t, int) else TYPE_CODES[t]
    body = content(obj)
    plain_size = 3 + len(body)
    if plain_size > MAX_OBJECT_SIZE:
        raise EncodeError(f"object 0x{obj['id']:04X} is {plain_size} bytes; the limit is {MAX_OBJECT_SIZE}")
    if compression != "off":
        packed = bytes([COMPRESSION_DEFLATE]) + deflate(body)
        if len(packed) < len(body):
            return header(obj["id"], code, obj.get("static"), True, revision) + packed
    return header(obj["id"], code, obj.get("static"), False, revision) + body


def descriptor(encoded):
    """The object description byte of an encoded object (used in TOC entities)."""
    return encoded[2]
