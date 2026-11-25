"""MSC data groups (ETSI TS 102 979 clause 8.1.1) and DAB packet mode
(ETSI EN 300 401 clause 5.3.2).

Journaline data groups have a fixed 2-byte header: no extension field, CRC
present, no segmentation, no user access field. Type 0 carries a JML object,
type 6 a block of management data (TOC). The packet layer is the same as
the one used by the MPBNL SPI WebFrontend.
"""

from .crc import crc16

DG_JML = 0x0
DG_MANAGEMENT = 0x6
MAX_DG_FIELD = 4092

PACKET_SIZES = (24, 48, 72, 96)


def datagroup(payload, dg_type, continuity=0, repetition=0):
    if len(payload) > MAX_DG_FIELD:
        raise ValueError(f"data group field is {len(payload)} bytes; the limit is {MAX_DG_FIELD}")
    hdr = bytes([0x40 | (dg_type & 0x0F), ((continuity & 0x0F) << 4) | (repetition & 0x0F)])
    body = hdr + bytes(payload)
    return body + crc16(body).to_bytes(2, "big")


def parse_datagroup(dg):
    """Returns (type, continuity, payload) or raises ValueError."""
    if len(dg) < 4:
        raise ValueError("data group too short")
    if crc16(dg[:-2]) != int.from_bytes(dg[-2:], "big"):
        raise ValueError("data group CRC error")
    b0 = dg[0]
    if b0 & 0x80 or not b0 & 0x40 or b0 & 0x20 or b0 & 0x10:
        raise ValueError("unsupported data group header flags for Journaline")
    return b0 & 0x0F, dg[1] >> 4, dg[2:-2]


def packet_size_for(bitrate):
    """Largest DAB packet size that fits a whole number of times into one 24 ms
    frame (bitrate x 3 bytes), as recommended by Opendigitalradio."""
    frame = int(bitrate) * 3
    return next(s for s in (96, 72, 48, 24) if frame % s == 0)


def _packet(size, address, data, first, last, index):
    hdr = bytes([
        (((size // 24) - 1) << 6) | ((index & 3) << 4) | (0x08 if first else 0)
        | (0x04 if last else 0) | ((address >> 8) & 0x03),
        address & 0xFF,
        len(data) & 0x7F,
    ])
    body = hdr + data + bytes(size - len(data) - 5)
    return body + crc16(body).to_bytes(2, "big")


def _required_size(n, max_size):
    if n > max_size - 5:
        return max_size
    for s in PACKET_SIZES:
        if n <= s - 5:
            return s
    return 96


def _split(data, pieces):
    base, extra = divmod(len(data), pieces)
    out, pos = [], 0
    for n in range(pieces):
        size = base + (1 if n < extra else 0)
        out.append(data[pos:pos + size])
        pos += size
    return out


def encode_packets(groups, address=1, size=96):
    """One pass of the carousel as packets. The packet count is made a multiple
    of four so the continuity index carries on without a break when the
    multiplexer loops the file; the last data group is spread over 1-3 extra
    packets to get there."""
    if not 1 <= address <= 1023:
        raise ValueError("packet address must be between 1 and 1023")
    if size not in PACKET_SIZES:
        raise ValueError("packet size must be one of %s" % (PACKET_SIZES,))
    if not groups:
        return []
    chunk = size - 5
    plans = [[dg[i:i + chunk] for i in range(0, len(dg), chunk)] for dg in groups]
    extra = -sum(len(p) for p in plans) % 4
    if extra:
        # every Journaline data group is at least 8 bytes, so it always splits
        plans[-1] = _split(groups[-1], len(plans[-1]) + extra)
    out = []
    index = -1
    for parts in plans:
        for n, part in enumerate(parts):
            index = (index + 1) % 4
            out.append(_packet(_required_size(len(part), size), address, part, n == 0, n == len(parts) - 1, index))
    return out


def parse_packets(stream):
    """Reassemble data groups from a packet stream, keyed by address.
    Returns {address: [datagroup bytes, ...]}; raises ValueError on a bad packet."""
    out, partial, pos = {}, {}, 0
    while pos < len(stream):
        size = ((stream[pos] >> 6) + 1) * 24
        pkt = stream[pos:pos + size]
        if len(pkt) < size:
            raise ValueError("truncated packet")
        if crc16(pkt[:-2]) != int.from_bytes(pkt[-2:], "big"):
            raise ValueError(f"packet CRC error at offset {pos}")
        first, last = bool(pkt[0] & 0x08), bool(pkt[0] & 0x04)
        addr = ((pkt[0] & 3) << 8) | pkt[1]
        data = pkt[3:3 + (pkt[2] & 0x7F)]
        if first:
            partial[addr] = bytearray()
        if addr in partial:
            partial[addr] += data
            if last:
                out.setdefault(addr, []).append(bytes(partial.pop(addr)))
        pos += size
    return out
