"""TOC management data blocks (ETSI TS 102 979 clause 6.2)."""

from .jml import MAX_OBJECT_SIZE

BLOCK_TYPE_TOC = 0x54  # "T"
HEADER_SIZE = 13  # type, revision, count, index, preceding id(2), object count(2), timeout(2), entity len, ext len(2)
ENTITY_SIZE = 3
MAX_ENTITIES = (MAX_OBJECT_SIZE - HEADER_SIZE) // ENTITY_SIZE  # 1359


def toc_blocks(entries, revision, timeout_minutes=0, max_entities=MAX_ENTITIES):
    """entries: [(object_id, description_byte), ...] for every object in the service.

    Returns the TOC fragments as a list of bytes. Entities are sorted by object
    ID; each fragment's 'preceding object ID' is the last ID of the previous
    fragment (0x0000 for the first). TOC blocks are never compressed."""
    entries = sorted(set((int(i), int(d) & 0xFF) for i, d in entries))
    if not entries:
        return []
    if len({i for i, _ in entries}) != len(entries):
        raise ValueError("duplicate object id in TOC")
    if not 0 <= int(timeout_minutes) <= 0xFFFF:
        raise ValueError("TOC timeout must be 0-65535 minutes")
    frags = [entries[i:i + max_entities] for i in range(0, len(entries), max_entities)]
    if len(frags) > 255:
        raise ValueError("too many objects for the TOC")
    out = []
    prev = 0
    for idx, frag in enumerate(frags):
        hdr = bytes([BLOCK_TYPE_TOC, revision & 0xFF, len(frags), idx]) + prev.to_bytes(2, "big") \
            + len(entries).to_bytes(2, "big") + int(timeout_minutes).to_bytes(2, "big") \
            + bytes([ENTITY_SIZE]) + (0).to_bytes(2, "big")
        body = b"".join(i.to_bytes(2, "big") + bytes([d]) for i, d in frag)
        out.append(hdr + body)
        prev = frag[-1][0]
    return out


def parse_toc(block):
    if len(block) < HEADER_SIZE or block[0] != BLOCK_TYPE_TOC:
        raise ValueError("not a TOC block")
    ent_len = block[10]
    ext = int.from_bytes(block[11:13], "big")
    pos = HEADER_SIZE + ext
    ents = []
    while pos + ent_len <= len(block) and ent_len >= 3:
        ents.append((int.from_bytes(block[pos:pos + 2], "big"), block[pos + 2]))
        pos += ent_len
    return {
        "revision": block[1], "block_count": block[2], "block_index": block[3],
        "preceding_id": int.from_bytes(block[4:6], "big"), "object_count": int.from_bytes(block[6:8], "big"),
        "timeout": int.from_bytes(block[8:10], "big"),
        "entity_length": ent_len, "entities": ents,
    }
