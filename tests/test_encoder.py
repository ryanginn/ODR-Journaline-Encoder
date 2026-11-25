import os
import subprocess
import tempfile
import unittest
import zlib
from datetime import datetime, timezone

from odr_jml.encoder import decode, jml, msc, service, toc
from odr_jml.encoder.crc import crc16

ROOT = {"id": 0, "type": "menu", "title": "Main", "items": [{"target": 1, "label": "News"}]}
NEWS = {"id": 1, "type": "text", "title": "Headline", "body": "Body text"}


class TestJml(unittest.TestCase):
    def test_header_bits(self):
        # figure 6: object type in b7-b5, static b4, compress b3, revision b2-b0
        self.assertEqual(jml.header(0x1234, jml.LIST, static=True, compressed=False, revision=5), b"\x12\x34\x95")
        self.assertEqual(jml.header(0, jml.MENU, compressed=True, revision=7)[2], 0x2F)

    def test_table1_menu_example(self):
        obj = {"id": 0, "type": "menu", "title": "Sports",
               "items": [{"target": 0xAABB, "label": "Bund"}, {"target": 0xCCDD, "label": "Seco"}]}
        self.assertEqual(jml.content(obj), b"\x01Sports\x02\xaa\xbbBund\x02\xcc\xddSeco")

    def test_table1_body_and_list(self):
        self.assertEqual(jml.content({"type": "text", "title": "T", "body": "Research"}), b"\x01T\x03Research")
        self.assertEqual(jml.content({"type": "list", "title": "Socc", "rows": [["TSV", "3:0"], ["Dort", "", "x"]]}),
                         b"\x01Socc\x04TSV\x053:0\x04Dort\x05\x05x")

    def test_markup(self):
        self.assertEqual(jml.text_bytes("a\nb"), b"a\x10b")
        self.assertEqual(jml.text_bytes("a **b** c"), b"a \x12b\x13 c")
        self.assertEqual(jml.text_bytes("intro\n---\nrest"), b"intro\x14rest")
        self.assertEqual(jml.text_bytes("Donau­dampf"), b"Donau\x11dampf")
        self.assertEqual(jml.text_bytes("a\x01\x02b\x7f"), b"ab")
        self.assertEqual(jml.text_bytes("a\nb", markup=False), b"a b")

    def test_data_section_continuation(self):
        # table 2 example: a 262-byte payload is 0x1A 0xFF <256> 0x1B 0x05 <6>
        ds = jml.data_section(0xFF, bytes(261))
        self.assertEqual(ds[:2], b"\x1a\xff")
        self.assertEqual(ds[258:260], b"\x1b\x05")
        self.assertEqual(len(ds), 2 + 256 + 2 + 6)
        self.assertEqual(jml.data_section(0x20, b"[ANY"), b"\x1a\x04\x20[ANY")

    def test_timeouts(self):
        when = datetime(2000, 1, 1, 1, 0, tzinfo=timezone.utc)
        self.assertEqual(jml.ds_absolute_timeout(when), b"\x1a\x03\x01\x00\x00\x04")
        self.assertEqual(jml.ds_relative_timeout(90), b"\x1a\x02\x02\x00\x5a")

    def test_link_and_positions(self):
        self.assertEqual(jml.ds_link("jml", 0x0005), b"\x1a\x03\x03\x00\x00\x05")
        self.assertEqual(jml.ds_link("phone", "+353 1 234", "Call"), b"\x1a\x10\x03\x03+353 1 234\x00Call")
        ds = jml.ds_positions([(-90, 180)])
        self.assertEqual(ds[3:6], (round(-90 * 92000) & 0xFFFFFF).to_bytes(3, "big"))

    def test_compression_only_when_smaller(self):
        small = jml.encode(dict(NEWS), compression="auto")
        self.assertFalse(small[2] & 0x08)
        big = dict(NEWS, body="repeat " * 200)
        enc = jml.encode(big, compression="auto")
        self.assertTrue(enc[2] & 0x08)
        self.assertEqual(enc[3], 0x08)
        self.assertEqual(zlib.decompress(enc[4:], -12), jml.content(big))
        self.assertFalse(jml.encode(big, compression="off")[2] & 0x08)

    def test_size_limit(self):
        with self.assertRaises(jml.EncodeError):
            jml.encode(dict(NEWS, body="x" * 5000))
        jml.encode(dict(NEWS, body="x" * (4092 - 3 - len(b"\x01Headline\x03"))))

    def test_short_last_row_padded(self):
        c = jml.content({"type": "list", "title": "T", "rows": [["abc"], ["x"]]})
        self.assertTrue(c.endswith(b"\x04x\x1a\x00\x00"))
        self.assertEqual(decode.decode(jml.encode({"id": 2, "type": "list", "title": "T",
                                                   "rows": [["abc"], ["x"]]}))["rows"], [["abc"], ["x"]])


class TestRoundTrip(unittest.TestCase):
    def test_all_types(self):
        objs = [
            dict(ROOT, static=True),
            dict(NEWS, body="Intro **hot**\n---\nMore " * 50, language="eng", lifetime=30,
                 expires="2031-05-01T12:00:00+00:00",
                 links=[{"type": "url", "address": "https://example.com", "label": "Web"},
                        {"type": "jml", "address": 0, "label": "Home"}]),
            {"id": 2, "type": "title", "title": "Ticker – ünïcödé"},
            {"id": 3, "type": "list", "title": "Table", "rows": [["a", "1"], ["b", "2"]], "positions": [(53.3, -6.2)]},
        ]
        for o in objs:
            d = decode.decode(jml.encode(o, revision=3))
            self.assertEqual(d["id"], o["id"])
            self.assertEqual(d["type"], o["type"])
            self.assertEqual(d["title"], o["title"])
            self.assertEqual(d["revision"], 3)
        d = decode.decode(jml.encode(objs[1]))
        self.assertTrue(d["compressed"])
        self.assertEqual(d["language"], "eng")
        self.assertEqual(d["lifetime"], 30)
        self.assertEqual(d["expires"], "2031-05-01T12:00:00+00:00")
        self.assertEqual(d["links"][0], {"type": "url", "address": "https://example.com", "label": "Web"})
        self.assertIn(("hl", True), d["body_segs"])
        self.assertIn(("intro",), d["body_segs"])
        d = decode.decode(jml.encode(objs[3]))
        self.assertEqual(d["rows"], [["a", "1"], ["b", "2"]])
        self.assertAlmostEqual(d["positions"][0][0], 53.3, places=4)
        d = decode.decode(jml.encode(objs[0]))
        self.assertEqual(d["items"][0]["target"], 1)
        self.assertTrue(d["static"])


class TestToc(unittest.TestCase):
    def test_layout(self):
        b = toc.toc_blocks([(5, 0x40), (0, 0x20)], revision=9, timeout_minutes=120)[0]
        self.assertEqual(b[:13], bytes([0x54, 9, 1, 0, 0, 0, 0, 2, 0, 120, 3, 0, 0]))
        self.assertEqual(b[13:], b"\x00\x00\x20\x00\x05\x40")

    def test_fragments(self):
        ents = [(i, 0x40) for i in range(10)]
        blocks = toc.toc_blocks(ents, 1, max_entities=4)
        self.assertEqual(len(blocks), 3)
        parsed = [toc.parse_toc(b) for b in blocks]
        self.assertEqual([p["block_index"] for p in parsed], [0, 1, 2])
        self.assertEqual([p["preceding_id"] for p in parsed], [0, 3, 7])
        self.assertTrue(all(p["object_count"] == 10 and p["block_count"] == 3 for p in parsed))


class TestMsc(unittest.TestCase):
    def test_datagroup_header(self):
        dg = msc.datagroup(b"abc", msc.DG_MANAGEMENT, continuity=17)
        self.assertEqual(dg[:2], b"\x46\x10")
        self.assertEqual(int.from_bytes(dg[-2:], "big"), crc16(dg[:-2]))
        self.assertEqual(msc.parse_datagroup(dg), (6, 1, b"abc"))
        with self.assertRaises(ValueError):
            msc.datagroup(bytes(4093), 0)

    def test_packets_round_trip(self):
        groups = [msc.datagroup(bytes([i]) * (i * 37 + 5), 0, i) for i in range(9)]
        for size in msc.PACKET_SIZES:
            pk = msc.encode_packets(groups, address=0x3FF, size=size)
            self.assertEqual(len(pk) % 4, 0)
            self.assertEqual(msc.parse_packets(b"".join(pk))[0x3FF], groups)

    def test_packet_sizes(self):
        self.assertEqual([msc.packet_size_for(b) for b in (8, 16, 24, 32, 40, 64)], [24, 48, 72, 96, 24, 96])


class TestService(unittest.TestCase):
    def test_validation(self):
        errs, warns = service.validate([dict(ROOT, items=[{"target": 9, "label": "x"}]),
                                        {"id": 4, "type": "text", "title": "", "body": ""}])
        msgs = " ".join(m for _, m in errs)
        self.assertIn("does not exist", msgs)
        self.assertIn("title is empty", msgs)
        self.assertIn("message text is empty", msgs)
        self.assertTrue(any("not reachable" in m for _, m in warns))
        errs, _ = service.validate([NEWS])
        self.assertTrue(any("root" in m for _, m in errs))
        errs, _ = service.validate([dict(ROOT, items=[{"target": 1, "label": "x"}] * 33), NEWS])
        self.assertTrue(any("at most 32" in m for _, m in errs))

    def test_hierarchy_limit(self):
        chain = [{"id": i, "type": "menu", "title": f"L{i}", "items": [{"target": i + 1, "label": "next"}]}
                 for i in range(21)] + [{"id": 21, "type": "title", "title": "deep"}]
        errs, _ = service.validate(chain)
        self.assertTrue(any("levels deep" in m for _, m in errs))
        self.assertEqual(service.hierarchy(chain)[21], 22)

    def test_revisions(self):
        r1 = service.next_revisions([ROOT, NEWS], {})
        self.assertEqual((r1["0"]["rev"], r1["1"]["rev"], r1["toc"]["rev"]), (0, 0, 0))
        r2 = service.next_revisions([ROOT, NEWS], r1)
        self.assertEqual(r2, r1)
        r3 = service.next_revisions([ROOT, dict(NEWS, body="changed")], r2)
        self.assertEqual((r3["0"]["rev"], r3["1"]["rev"], r3["toc"]["rev"]), (0, 1, 1))
        r4 = service.next_revisions([ROOT], r3)
        self.assertEqual(r4["toc"]["rev"], 2)
        prev = {"1": {"hash": "x", "rev": 7}, "toc": {"rev": 255, "hash": ""}}
        r5 = service.next_revisions([NEWS], prev)
        self.assertEqual((r5["1"]["rev"], r5["toc"]["rev"]), (0, 0))

    def test_schedule_weights(self):
        order = service.schedule([("a", 4), ("b", 1), ("c", 2)])
        self.assertEqual(sorted(order), ["a"] * 4 + ["b"] + ["c"] * 2)
        # never the same object twice in a row when others are waiting
        self.assertNotIn(("a", "a"), list(zip(order, order[1:])))

    def test_build(self):
        r = service.build([ROOT, NEWS, {"id": 2, "type": "title", "title": "T"}])
        types = [msc.parse_datagroup(g)[0] for g in r["groups"]]
        self.assertIn(msc.DG_MANAGEMENT, types)
        self.assertEqual([msc.parse_datagroup(g)[1] for g in r["groups"]], [i % 16 for i in range(len(types))])
        ents = toc.parse_toc(r["toc_blocks"][0])["entities"]
        self.assertEqual([e[0] for e in ents], [0, 1, 2])
        s = service.stream(r["groups"], 16, 1)
        self.assertEqual(msc.parse_packets(s)[1], r["groups"])
        self.assertEqual(service.stream(r["groups"], 16, 1, datagroup_mode=True), b"".join(r["groups"]))


DECODER = os.environ.get("JML_DECODER") or os.path.join(os.path.dirname(__file__), "..", "tools", "decoder-check", "build", "jml-decode")


@unittest.skipUnless(os.path.exists(DECODER), "Fraunhofer decoder not built (tools/decoder-check/build.sh)")
class TestFraunhoferDecoder(unittest.TestCase):
    def test_decodes(self):
        objs = [dict(ROOT, items=[{"target": 1, "label": "News"}, {"target": 2, "label": "Table"}], static=True),
                dict(NEWS, body="Long " * 300),
                {"id": 2, "type": "list", "title": "Table", "rows": [["a", "1"], ["b"]]}]
        r = service.build(objs)
        groups = msc.parse_packets(service.stream(r["groups"], 24, 3))[3]
        with tempfile.NamedTemporaryFile(delete=False) as f:
            for g in groups:
                f.write(len(g).to_bytes(2, "big") + g)
        try:
            out = subprocess.run([DECODER, f.name], capture_output=True, text=True, check=True).stdout
        finally:
            os.unlink(f.name)
        self.assertIn("id=0000 type=menu static=1 rev=0 title=[Main] items=2", out)
        self.assertIn("id=0001 type=plain", out)
        self.assertIn("item link=0001 [News]", out)
        self.assertIn("title=[Table] items=3", out)
        self.assertNotIn("Error", out)


if __name__ == "__main__":
    unittest.main()
