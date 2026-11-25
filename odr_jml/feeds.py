"""RSS 2.0 / RSS 1.0 (RDF) / Atom feeds turned into Journaline objects.

A feed is one object in the service tree (its jid):
  menu    a menu of headlines, each linking to a plain-text message with the story
  ticker  a title-only message with the latest headline (news ticker)
  list    a list message, one headline per row
Message objects for menu-mode stories get stable object IDs from the feed's
id_map (keyed by item GUID/link), allocated from FEED_ID_BASE upwards."""

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

import xml.etree.ElementTree as StdET

from defusedxml import ElementTree as ET

from .encoder import jml

FEED_ID_BASE = 0x8000
MAX_ITEMS = 32
# leave room in the 4 092-byte object for header, title and codes
MAX_BODY_BYTES = 3600


class FeedError(Exception):
    pass


# --- HTML to text ------------------------------------------------------------------------

class _Text(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "blockquote", "section", "article"}
    SKIP = {"script", "style", "head", "noscript", "iframe", "figure", "figcaption"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_to_text(s):
    if not s:
        return ""
    if "<" in s:
        p = _Text()
        try:
            p.feed(s)
            p.close()
            s = "".join(p.out)
        except Exception:
            s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("\xa0", " ")
    lines = [re.sub(r"[ \t\r\f\v]+", " ", l).strip() for l in s.split("\n")]
    out, blank = [], False
    for l in lines:
        if l:
            out.append(l)
            blank = False
        elif out and not blank:
            out.append("")
            blank = True
    return "\n".join(out).strip()


def one_line(s):
    return re.sub(r"\s+", " ", html_to_text(s)).strip()


def fit_bytes(text, limit):
    """Truncate text so its UTF-8 encoding fits in `limit` bytes, on a word boundary."""
    b = text.encode("utf-8")
    if len(b) <= limit:
        return text
    cut = b[:limit - 3].decode("utf-8", "ignore")
    sp = cut.rfind(" ")
    if sp > len(cut) * 0.7:
        cut = cut[:sp]
    return cut.rstrip() + "…"


# --- parsing -----------------------------------------------------------------------------

def _local(tag):
    return tag.rsplit("}", 1)[-1].lower() if isinstance(tag, str) else ""


def _child(el, *names):
    for c in el:
        if _local(c.tag) in names:
            return c
    return None


def _text(el, *names):
    c = _child(el, *names)
    if c is None:
        return ""
    if _local(c.tag) == "content" and c.get("type") in ("xhtml",):
        return "".join(c.itertext())
    if len(c):  # markup inside the element (not escaped)
        return (c.text or "") + "".join(StdET.tostring(x, encoding="unicode") for x in c)
    return c.text or ""


def _date(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.isoformat()


def parse(data):
    """Parse feed bytes. Returns {"title": str, "items": [{guid, title, text, published}]}."""
    try:
        root = ET.fromstring(data)
    except Exception as e:
        raise FeedError(f"not a valid RSS/Atom feed ({e.__class__.__name__})")
    kind = _local(root.tag)
    entries, title = [], ""
    if kind == "rss":
        ch = _child(root, "channel")
        if ch is None:
            raise FeedError("RSS feed has no channel")
        title = one_line(_text(ch, "title"))
        entries = [c for c in ch if _local(c.tag) == "item"]
    elif kind == "rdf":
        ch = _child(root, "channel")
        title = one_line(_text(ch, "title")) if ch is not None else ""
        entries = [c for c in root if _local(c.tag) == "item"]
    elif kind == "feed":
        title = one_line(_text(root, "title"))
        entries = [c for c in root if _local(c.tag) == "entry"]
    else:
        raise FeedError(f"unsupported feed type <{kind}>")
    items = []
    for e in entries:
        t = one_line(_text(e, "title"))
        if kind == "feed":
            body = _text(e, "content") or _text(e, "summary")
            link_el = _child(e, "link")
            link = link_el.get("href", "") if link_el is not None else ""
            guid = _text(e, "id") or link
            pub = _date(_text(e, "updated") or _text(e, "published"))
        else:
            body = _text(e, "encoded") or _text(e, "description")
            link = _text(e, "link").strip()
            guid = _text(e, "guid").strip() or link
            pub = _date(_text(e, "pubdate") or _text(e, "date"))
        text = html_to_text(body)
        if not t and not text:
            continue
        if not t:
            t = fit_bytes(one_line(text), 120)
        guid = guid or hashlib.sha1((t + text).encode()).hexdigest()
        items.append({"guid": guid[:500], "title": t[:300], "text": text[:20000], "published": pub})
    return {"title": title, "items": items}


# --- objects -----------------------------------------------------------------------------

def _stamp(item, tz):
    if not item.get("published"):
        return ""
    try:
        return datetime.fromisoformat(item["published"]).astimezone(tz).strftime("%H:%M")
    except ValueError:
        return ""


def assign_ids(feed, used):
    """Give each current item (in menu mode) a stable object ID. `used` holds
    every ID taken by other objects in the service. Returns the new id_map."""
    items = feed["items"][:feed["max_items"]]
    old = feed.get("id_map") or {}
    if feed["mode"] != "menu":
        return {}
    keep = {g: i for g, i in old.items() if any(it["guid"] == g for it in items) and i not in used}
    taken = set(used) | set(keep.values())
    nxt = FEED_ID_BASE
    for it in items:
        if it["guid"] in keep:
            continue
        while nxt in taken:
            nxt += 1
        if nxt > jml.MAX_FREE_ID:
            raise FeedError("no free object IDs left for feed stories")
        keep[it["guid"]] = nxt
        taken.add(nxt)
    return keep


def objects(feed, tz=timezone.utc):
    """The JML object dicts this feed contributes (container first)."""
    items = feed["items"][:feed["max_items"]]
    title = feed["title"] or feed["name"] or "News"
    jid = feed["jid"]
    static = bool(feed.get("static", 1))
    if feed["mode"] == "ticker":
        head = items[0]["title"] if items else title
        if items and feed.get("show_time") and _stamp(items[0], tz):
            head = f"{_stamp(items[0], tz)} {head}"
        return [{"id": jid, "type": "title", "title": fit_bytes(head, 3800), "static": static}]
    if not items:
        return [{"id": jid, "type": "title", "title": f"{title}: no stories at the moment", "static": static}]
    if feed["mode"] == "list":
        rows = []
        for it in items:
            rows.append([_stamp(it, tz), it["title"]] if feed.get("show_time") else [it["title"]])
        out = {"id": jid, "type": "list", "title": title, "rows": rows, "static": static}
        while len(jml.content(out)) > 4000 and len(out["rows"]) > 1:
            out["rows"].pop()
        return [out]
    id_map = feed.get("id_map") or {}
    menu = {"id": jid, "type": "menu", "title": title, "items": [], "static": static}
    stories = []
    for it in items[:jml.MAX_MENU_ITEMS]:
        sid = id_map.get(it["guid"])
        if sid is None:
            continue
        label = f"{_stamp(it, tz)} {it['title']}" if feed.get("show_time") and _stamp(it, tz) else it["title"]
        menu["items"].append({"target": sid, "label": fit_bytes(label, 200)})
        story_title = fit_bytes(it["title"], 300)
        body = it["text"] if feed.get("item_text", "description") == "description" else ""
        if not body.strip():
            body = it["title"]
        stamp = _stamp(it, tz)
        if stamp and feed.get("show_time"):
            story_title = f"{story_title} ({stamp})"
        stories.append({"id": sid, "type": "text", "title": story_title,
                        "body": fit_bytes(body, MAX_BODY_BYTES - len(story_title.encode())), "static": False})
    return [menu] + stories


def content_hash(items):
    return hashlib.sha1(json.dumps(items, sort_keys=True).encode()).hexdigest()
