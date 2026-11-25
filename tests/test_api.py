"""End-to-end API tests using the Flask test client."""
import http.server
import json
import os
import shutil
import tempfile
import threading
import time
import unittest

from odr_jml import __main__ as cli, build, config, db, scheduler, security
from odr_jml.encoder import decode, msc
from odr_jml.web import create_app

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
<title>Demo News</title>
<item><title>First &amp; foremost</title><guid>a1</guid><pubDate>Tue, 24 Nov 2026 10:00:00 GMT</pubDate>
<description>&lt;p&gt;Hello &lt;b&gt;world&lt;/b&gt;&lt;/p&gt;&lt;p&gt;Second paragraph&lt;/p&gt;</description></item>
<item><title>Second story</title><guid>a2</guid>
<content:encoded><![CDATA[<div>Body <script>x()</script>two</div>]]></content:encoded></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Atom</title>
<entry><title>Atom one</title><id>urn:1</id><updated>2026-11-24T10:00:00Z</updated><summary>Sum</summary></entry>
</feed>"""


class _Handler(http.server.BaseHTTPRequestHandler):
    feeds = {}

    def do_GET(self):
        body = self.feeds.get(self.path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/rss+xml")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cfg = dict(config.DEFAULTS, data_dir=os.path.join(self.dir, "data"))
        cli.init(self.cfg)
        security.setup_limiter.hits.clear()
        security.login_limiter.hits.clear()
        self.token = cli.setup_token(self.cfg)
        self.app = create_app(self.cfg)
        self.c = self.app.test_client()
        self.csrf = None
        _Handler.feeds = {"/news.xml": RSS, "/atom.xml": ATOM}

    def tearDown(self):
        db._local.conn.close()
        db._local.conn = None
        shutil.rmtree(self.dir)

    def call(self, method, url, body=None, client=None, csrf=None, **kw):
        c = client or self.c
        headers = {"X-Requested-With": "odr-jml"}
        tok = csrf if csrf is not None else self.csrf
        if tok:
            headers["X-CSRF-Token"] = tok
        if body is not None:
            kw["json"] = body
        r = getattr(c, method)(url, headers=headers, **kw)
        return r.status_code, r.get_json(silent=True)

    def ok(self, method, url, body=None, **kw):
        st, data = self.call(method, url, body, **kw)
        self.assertEqual(st, 200, data)
        return data

    def login_admin(self):
        self.ok("post", "/api/setup", {"token": self.token, "username": "rian", "password": "correct horse battery"})
        self.csrf = self.call("get", "/api/state")[1]["csrf"]

    def new_service(self, name="News", **kw):
        body = {"name": name, "output_path": os.path.join(self.dir, f"{name.lower()}.dat"), "bitrate": 16}
        body.update(kw)
        return self.ok("post", "/api/services", body)["id"]

    # ------------------------------------------------------------------------------------

    def test_setup_and_csrf(self):
        st, _ = self.call("post", "/api/setup", {"token": "nope", "username": "xyz", "password": "y" * 12})
        self.assertEqual(st, 403)
        self.login_admin()
        st, _ = self.call("post", "/api/services", {"name": "x"}, csrf="bad")
        self.assertEqual(st, 403)
        st, _ = self.call("post", "/api/setup", {"token": self.token, "username": "abc", "password": "y" * 12})
        self.assertEqual(st, 409)

    def test_service_starter_and_publish(self):
        self.login_admin()
        sid = self.new_service()
        s = self.ok("get", f"/api/services/{sid}")
        self.assertEqual([o["jid"] for o in s["object_list"]], [0, 1])
        self.assertEqual(s["errors"], [])
        self.assertTrue(self.ok("get", "/api/status")["dirty_since"])
        bid = build.run("test", apply_changes=True)
        b = db.q1("SELECT * FROM builds WHERE id = ?", (bid,))
        self.assertEqual(b["status"], "ok", b["message"])
        with open(os.path.join(self.dir, "news.dat"), "rb") as f:
            groups = msc.parse_packets(f.read())[1]
        objs = {}
        for g in groups:
            t, _, payload = msc.parse_datagroup(g)
            if t == 0:
                d = decode.decode(payload)
                objs[d["id"]] = d
        self.assertEqual(objs[0]["items"][0]["target"], 1)
        self.assertEqual(objs[1]["title"], "Welcome to News")
        stats = json.loads(b["stats"])["services"][0]
        self.assertGreater(stats["cycle_seconds"], 0)

    def test_objects_crud_and_links(self):
        self.login_admin()
        sid = self.new_service()
        r = self.ok("post", f"/api/services/{sid}/objects", {"type": "list", "title": "Results", "parent": 0,
                                                             "label": "Football",
                                                             "rows": [["A - B", "1:0"], ["C - D", "2:2"]]})
        jid = r["jid"]
        self.assertEqual(jid, 2)
        root = next(o for o in self.ok("get", f"/api/services/{sid}")["object_list"] if o["jid"] == 0)
        self.assertEqual(root["items"][-1], {"target": 2, "label": "Football"})
        # renumbering keeps the menu link pointing at it
        self.ok("put", f"/api/objects/{r['id']}", {"jid": 0x20})
        root = next(o for o in self.ok("get", f"/api/services/{sid}")["object_list"] if o["jid"] == 0)
        self.assertEqual(root["items"][-1]["target"], 0x20)
        o = self.ok("get", f"/api/objects/{r['id']}")
        self.assertEqual(o["referenced_by"][0]["jid"], 0)
        # too large is refused on save
        st, d = self.call("put", f"/api/objects/{r['id']}", {"rows": [["x" * 300, "y" * 300]] * 20})
        self.assertEqual(st, 400)
        self.assertIn("4092", d["error"])
        # duplicate id refused
        st, _ = self.call("post", f"/api/services/{sid}/objects", {"type": "title", "title": "T", "jid": 1})
        self.assertEqual(st, 400)
        # deleting removes links; the root can't be deleted
        self.ok("delete", f"/api/objects/{r['id']}")
        root = next(o for o in self.ok("get", f"/api/services/{sid}")["object_list"] if o["jid"] == 0)
        self.assertEqual([i["target"] for i in root["items"]], [1])
        st, _ = self.call("delete", f"/api/objects/{root['id']}")
        self.assertEqual(st, 400)

    def test_validation_and_preview(self):
        self.login_admin()
        sid = self.new_service()
        r = self.ok("post", f"/api/services/{sid}/objects", {"type": "text", "title": "Story", "body": "Hi **there**\n---\nmore",
                                                             "links": [{"type": "phone", "address": "+353 1 234", "label": "Call"}],
                                                             "expires": "2099-01-01T00:00"})
        p = self.ok("get", f"/api/services/{sid}/preview")
        self.assertTrue(any("not reachable" in w["message"] for w in p["warnings"]))
        story = p["objects"][str(r["jid"])]
        self.assertEqual(story["links"][0]["address"], "+353 1 234")
        self.assertIn(["hl", True], story["body_segs"])
        self.assertIsNotNone(p["estimate"])
        st, d = self.call("post", f"/api/services/{sid}/objects",
                          {"type": "text", "title": "x", "links": [{"type": "phone", "address": "0123"}]})
        self.assertEqual(st, 400)
        st, d = self.call("post", f"/api/services/{sid}/objects", {"type": "text", "title": "x", "language": "english"})
        self.assertEqual(st, 400)

    def test_expired_objects_are_dropped(self):
        self.login_admin()
        sid = self.new_service()
        r = self.ok("post", f"/api/services/{sid}/objects", {"type": "title", "title": "Old", "parent": 0,
                                                             "expires": "2001-01-01T00:00:00+00:00"})
        p = self.ok("get", f"/api/services/{sid}/preview")
        self.assertNotIn(str(r["jid"]), p["objects"])
        self.assertEqual([i["target"] for i in p["objects"]["0"]["items"]], [1])

    def test_feeds(self):
        self.login_admin()
        self.ok("put", "/api/settings", {"allow_private_urls": True})
        sid = self.new_service()
        t = self.ok("post", "/api/feeds/test", {"url": self.base + "/news.xml"})
        self.assertEqual(t["count"], 2)
        self.assertEqual(t["items"][0]["title"], "First & foremost")
        self.assertEqual(t["items"][0]["text"], "Hello world\n\nSecond paragraph")
        self.assertEqual(t["items"][1]["text"], "Body two")
        f = self.ok("post", f"/api/services/{sid}/feeds", {"url": self.base + "/news.xml", "mode": "menu",
                                                           "title": "Headlines", "parent": 0, "label": "News"})
        self.assertIsNone(f["error"])
        p = self.ok("get", f"/api/services/{sid}/preview")
        menu = p["objects"][str(f["jid"])]
        self.assertEqual(menu["type"], "menu")
        self.assertEqual([i["label"] for i in menu["items"]], ["First & foremost", "Second story"])
        story_ids = [i["target"] for i in menu["items"]]
        self.assertTrue(all(i >= 0x8000 for i in story_ids))
        self.assertEqual(p["objects"][str(story_ids[0])]["body"], "Hello world\n\nSecond paragraph")
        self.assertEqual(p["errors"], [])
        # a new story keeps the old ones' ids
        _Handler.feeds["/news.xml"] = RSS.replace(b"<item><title>First", b"<item><title>Newest</title><guid>a0</guid>"
                                                  b"<description>n</description></item><item><title>First")
        self.ok("post", f"/api/feeds/{f['id']}/refresh")
        menu = self.ok("get", f"/api/services/{sid}/preview")["objects"][str(f["jid"])]
        self.assertEqual([i["target"] for i in menu["items"]][1:], story_ids)
        # ticker and list modes; atom
        t = self.ok("post", f"/api/services/{sid}/feeds", {"url": self.base + "/atom.xml", "mode": "ticker"})
        l = self.ok("post", f"/api/services/{sid}/feeds", {"url": self.base + "/news.xml", "mode": "list",
                                                           "title": "List", "show_time": True})
        p = self.ok("get", f"/api/services/{sid}/preview")
        self.assertEqual(p["objects"][str(t["jid"])]["title"], "Atom one")
        self.assertEqual(p["objects"][str(l["jid"])]["type"], "list")
        # failing feed keeps its items and reports
        _Handler.feeds.pop("/news.xml")
        st, d = self.call("post", f"/api/feeds/{f['id']}/refresh")
        self.assertEqual(st, 400)
        menu = self.ok("get", f"/api/services/{sid}/preview")["objects"][str(f["jid"])]
        self.assertEqual(len(menu["items"]), 3)
        self.assertTrue(self.ok("get", "/api/services")[0]["feed_errors"])
        # private addresses are refused unless allowed
        self.ok("put", "/api/settings", {"allow_private_urls": False})
        st, d = self.call("post", "/api/feeds/test", {"url": self.base + "/atom.xml"})
        self.assertEqual(st, 400)

    def test_scheduled_rebuild_picks_up_feed_changes(self):
        self.login_admin()
        self.ok("put", "/api/settings", {"allow_private_urls": True, "refresh_minutes": 5})
        sid = self.new_service()
        f = self.ok("post", f"/api/services/{sid}/feeds", {"url": self.base + "/news.xml", "mode": "ticker", "parent": 0})
        build.run("apply", apply_changes=True)
        _Handler.feeds["/news.xml"] = RSS.replace(b"First &amp; foremost", b"Breaking")
        scheduler.tick(now=time.time())
        self.assertTrue(scheduler.tick(now=time.time() + 600))
        with open(os.path.join(self.dir, "news.dat"), "rb") as fh:
            groups = msc.parse_packets(fh.read())[1]
        titles = {decode.decode(msc.parse_datagroup(g)[2])["title"] for g in groups if msc.parse_datagroup(g)[0] == 0}
        self.assertIn("Breaking", titles)
        rev = json.loads(db.q1("SELECT revisions FROM services WHERE id = ?", (sid,))["revisions"])
        self.assertEqual(rev[str(f["jid"])]["rev"], 1)

    def test_two_services(self):
        self.login_admin()
        a = self.new_service("Alpha")
        b = self.new_service("Beta")
        sa, sb = self.ok("get", f"/api/services/{a}"), self.ok("get", f"/api/services/{b}")
        self.assertNotEqual(sa["packet_address"], sb["packet_address"])
        self.assertNotEqual(sa["mux"]["subchannel_uid"], sb["mux"]["subchannel_uid"])
        st, d = self.call("patch", f"/api/services/{b}", {"output_path": sa["output_path"]})
        self.assertEqual(st, 400)
        bid = build.run("test", apply_changes=True)
        self.assertEqual(db.q1("SELECT status FROM builds WHERE id = ?", (bid,))["status"], "ok")
        self.assertTrue(os.path.exists(sa["output_path"]) and os.path.exists(sb["output_path"]))
        # one broken service does not stop the other
        root = next(o for o in sb["object_list"] if o["jid"] == 0)
        self.ok("put", f"/api/objects/{root['id']}", {"items": [{"target": 0x99, "label": "missing"}]})
        bid = build.run("test", apply_changes=True)
        row = db.q1("SELECT * FROM builds WHERE id = ?", (bid,))
        self.assertEqual(row["status"], "error")
        self.assertIn("Wrote 1 of 2", row["message"])
        self.assertIn("0x0099", row["message"])

    def test_mux_snippet_and_config_read(self):
        self.login_admin()
        sid = self.new_service()
        mux = """ensemble {
    id 0xc1a5
    ecc 0xe3
    label "Test Mux"
}
subchannels {
    sub-a { type dabplus
        id 1 }
    sub-b {
        type packet
        id 7
    }
}
"""
        r = self.c.post("/api/mux/read", data={"file": (__import__("io").BytesIO(mux.encode()), "t.mux"),
                                               "save_ensemble": "1"},
                        headers={"X-Requested-With": "odr-jml", "X-CSRF-Token": self.csrf})
        info = r.get_json()
        self.assertEqual(info["ensemble"], {"ecc": "e3", "eid": "c1a5", "label": "Test Mux"})
        self.assertEqual(info["free_subchannel_id"], 8)
        sn = self.ok("get", f"/api/services/{sid}/mux")
        self.assertIn("userapp \"journaline\"", sn["info"]["components"])
        self.assertIn("datagroup true", sn["info"]["components"])
        comp = sn["json"]["components"]["comp-journaline"]
        self.assertEqual(comp["user-applications"], {"userapp": "journaline"})
        self.assertTrue(comp["datagroup"])
        self.assertTrue(sn["json"]["services"]["srv-journaline"]["id"].startswith("0xe3c1a5"))
        self.assertEqual(self.ok("get", "/api/state")["mux_name"], "Test Mux")

    def test_export_import(self):
        self.login_admin()
        self.ok("put", "/api/settings", {"allow_private_urls": True})
        a = self.new_service("Alpha")
        self.ok("post", f"/api/services/{a}/feeds", {"url": self.base + "/news.xml", "mode": "menu", "parent": 0})
        r = self.c.get(f"/api/services/{a}/export", headers={"X-Requested-With": "odr-jml"})
        data = json.loads(r.data)
        b = self.new_service("Beta")
        res = self.ok("post", f"/api/services/{b}/import", {"data": data})
        self.assertEqual(res, {"objects": 2, "feeds": 1})
        st, _ = self.call("post", f"/api/services/{b}/import", {"data": {"format": "x"}})
        self.assertEqual(st, 400)

    def test_editor_role(self):
        self.login_admin()
        r = self.ok("post", "/api/users", {"username": "editor1", "role": "editor", "password": "editor password 1"})
        st, _ = self.call("post", "/api/users", {"username": "st", "role": "station"})
        self.assertEqual(st, 400)
        ed = self.app.test_client()
        h = {"X-Requested-With": "odr-jml"}
        ed.post("/api/login", json={"username": "editor1", "password": "editor password 1"}, headers=h)
        csrf = ed.get("/api/state").get_json()["csrf"]
        st, _ = self.call("post", "/api/account/password", {"current": "editor password 1", "new": "editor password 2"},
                          client=ed, csrf=csrf)
        self.assertEqual(st, 200)
        st, _ = self.call("post", "/api/services", {"name": "Ed's"}, client=ed, csrf=csrf)
        self.assertEqual(st, 200)
        st, _ = self.call("get", "/api/users", client=ed, csrf=csrf)
        self.assertEqual(st, 403)
        st, _ = self.call("put", "/api/settings", {"mux_name": "x"}, client=ed, csrf=csrf)
        self.assertEqual(st, 403)
        self.assertTrue(r["id"])

    def test_move_links(self):
        self.login_admin()
        sid = self.new_service()
        sub = self.ok("post", f"/api/services/{sid}/objects", {"type": "menu", "title": "Sport", "parent": 0})["jid"]
        a = self.ok("post", f"/api/services/{sid}/objects", {"type": "title", "title": "A", "parent": 0})["jid"]
        b = self.ok("post", f"/api/services/{sid}/objects", {"type": "title", "title": "B", "parent": 0})["jid"]
        items = lambda jid: [i["target"] for i in next(o for o in self.ok("get", f"/api/services/{sid}")["object_list"]
                                                      if o["jid"] == jid)["items"]]
        self.assertEqual(items(0), [1, sub, a, b])
        # reorder within the root: move B before the welcome message, then A to the end
        self.ok("post", f"/api/services/{sid}/move", {"target": b, "from": 0, "from_index": 3, "to": 0, "index": 0})
        self.assertEqual(items(0), [b, 1, sub, a])
        self.ok("post", f"/api/services/{sid}/move", {"target": b, "from": 0, "from_index": 0, "to": 0, "index": 4})
        self.assertEqual(items(0), [1, sub, a, b])
        # move A into the sport menu (it needs a link before it can be valid anyway)
        st, d = self.call("post", f"/api/services/{sid}/move", {"target": a, "from": 0, "from_index": 2, "to": sub})
        self.assertEqual(st, 200, d)
        self.assertEqual(items(0), [1, sub, b])
        self.assertEqual(items(sub), [a])
        # copy B into sport too (keeps its root link and label)
        self.ok("post", f"/api/services/{sid}/move", {"target": b, "from": 0, "to": sub, "index": 0, "copy": True})
        self.assertEqual(items(sub), [b, a])
        self.assertEqual(items(0), [1, sub, b])
        # duplicates, self-nesting and moving a menu into its own sub-menu are refused
        st, _ = self.call("post", f"/api/services/{sid}/move", {"target": b, "from": 0, "to": sub})
        self.assertEqual(st, 400)
        st, _ = self.call("post", f"/api/services/{sid}/move", {"target": sub, "from": 0, "to": sub})
        self.assertEqual(st, 400)
        inner = self.ok("post", f"/api/services/{sid}/objects", {"type": "menu", "title": "Inner", "parent": sub})["jid"]
        st, d = self.call("post", f"/api/services/{sid}/move", {"target": sub, "from": 0, "to": inner})
        self.assertEqual(st, 400)
        self.assertIn("own sub-menus", d["error"])
        # unlink (drop on "not linked")
        self.ok("post", f"/api/services/{sid}/move", {"target": b, "from": sub, "from_index": 0, "to": None})
        self.assertEqual(items(sub), [a, inner])
        # an unlinked object can be linked into a menu
        c = self.ok("post", f"/api/services/{sid}/objects", {"type": "title", "title": "Loose"})["jid"]
        self.ok("post", f"/api/services/{sid}/move", {"target": c, "to": 0, "index": 1})
        root = next(o for o in self.ok("get", f"/api/services/{sid}")["object_list"] if o["jid"] == 0)
        self.assertEqual(root["items"][1], {"target": c, "label": "Loose"})
        # feed menus can't be edited by dragging into them
        self.ok("put", "/api/settings", {"allow_private_urls": True})
        f = self.ok("post", f"/api/services/{sid}/feeds", {"url": self.base + "/news.xml", "mode": "menu"})
        st, _ = self.call("post", f"/api/services/{sid}/move", {"target": c, "to": f["jid"]})
        self.assertEqual(st, 400)

    def test_attach_to_audio_stations(self):
        self.login_admin()
        sid = self.new_service()
        s = self.ok("get", f"/api/services/{sid}")
        mux = dict(s["mux"], standalone=False, linked=[{"uid": "srv-radio1", "label": "Radio 1"}, {"uid": "srv-radio2"}])
        self.ok("patch", f"/api/services/{sid}", {"mux": mux})
        sn = self.ok("get", f"/api/services/{sid}/mux")
        self.assertNotIn("services", sn["json"])
        comps = sn["json"]["components"]
        self.assertEqual(sorted(c["service"] for c in comps.values()), ["srv-radio1", "srv-radio2"])
        self.assertTrue(all(c["subchannel"] == "sub-journaline" and c["datagroup"] for c in comps.values()))
        self.assertIn("service srv-radio1", sn["info"]["components"])
        both = dict(mux, standalone=True)
        self.ok("patch", f"/api/services/{sid}", {"mux": both})
        sn = self.ok("get", f"/api/services/{sid}/mux")
        self.assertEqual(len(sn["json"]["components"]), 3)
        st, _ = self.call("patch", f"/api/services/{sid}", {"mux": dict(mux, linked=[{"uid": "bad uid!"}])})
        self.assertEqual(st, 400)
        none = dict(mux, standalone=False, linked=[])
        self.ok("patch", f"/api/services/{sid}", {"mux": none})
        self.assertTrue(any("can't find it" in w for w in self.ok("get", f"/api/services/{sid}/mux")["warnings"]))

    def test_link_text_follows_title(self):
        self.login_admin()
        sid = self.new_service()
        r = self.ok("post", f"/api/services/{sid}/objects", {"type": "text", "title": "Seo é Nuacht MPB", "parent": 0})
        label = lambda: next(i["label"] for i in next(o for o in self.ok("get", f"/api/services/{sid}")["object_list"]
                                                      if o["jid"] == 0)["items"] if i["target"] == r["jid"])
        self.assertEqual(label(), "Seo é Nuacht MPB")
        self.ok("put", f"/api/objects/{r['id']}", {"title": "Welcome"})
        self.assertEqual(label(), "Welcome")
        # text changed on purpose stays put when the title changes again
        self.ok("post", f"/api/services/{sid}/link-text", {"menu": 0, "target": r["jid"], "label": "Fáilte"})
        self.ok("put", f"/api/objects/{r['id']}", {"title": "Hello"})
        self.assertEqual(label(), "Fáilte")
        st, _ = self.call("post", f"/api/services/{sid}/link-text", {"menu": 0, "target": 0x77, "label": "x"})
        self.assertEqual(st, 409)
        st, _ = self.call("post", f"/api/services/{sid}/link-text", {"menu": 0, "target": r["jid"], "label": ""})
        self.assertEqual(st, 400)
        # long titles: the link made at creation is cut to 60 characters and still follows
        long = self.ok("post", f"/api/services/{sid}/objects", {"type": "title", "title": "x" * 80, "parent": 0})
        self.ok("put", f"/api/objects/{long['id']}", {"title": "Short"})
        root = next(o for o in self.ok("get", f"/api/services/{sid}")["object_list"] if o["jid"] == 0)
        self.assertEqual(next(i["label"] for i in root["items"] if i["target"] == long["jid"]), "Short")


if __name__ == "__main__":
    unittest.main()
