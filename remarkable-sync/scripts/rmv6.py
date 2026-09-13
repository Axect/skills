"""Parser for the reMarkable v6 (.rm) lines format used by firmware 3.x.

Format reference: YakBarber/remarkable_file_format rmv6.ksy (Kaitai spec,
reverse-engineered), extended here with block flags the spec misses
(0x08010100, 0x0a010000, 0x0d010000 observed in real 2024-2026 files).

Layout: 43-byte text header, frontmatter (~200 bytes, page-level metadata),
then size-type-value blocks until EOF:
    u32 len_body, u32 flag, body[len_body]
Known flags:
    0x01010100 layer_def   (one per layer, in order)
    0x02020100 layer_names
    0x04010100 layer_info
    0x07010100 text_def
    0x05020200 line_def    (one per stroke)
    others: opaque, skipped

line_def body:
    1f <layer u16> 2f <line u16> 3f <prev u16> 4f <id u16> 54
    <done u32>  [done != 0 -> no payload]
    6c <blklen u32> 0314 <pen u32> 24 <color u32> 38 00000000 00
    <brush f32> 44 00000000 00 5c <points_len u32>
    points_len/14 points: x f32, y f32, speed u1, pad u1, width u1, pad u1,
    direction u1, pressure u1
    6f 0001

Coordinates: x is centered (origin at page center, +-702 for 1404 px wide),
y from top. Converted to rmrl's top-left-origin pixel coordinates here.
Pen ids >= 12 are the fw3 generation; rmrl's PEN_MAPPING already covers them.
"""

import struct
from collections import namedtuple

Layer = namedtuple("Layer", ["strokes", "name"])
Stroke = namedtuple("Stroke", ["pen", "color", "unk1", "width", "unk2", "segments"])
Segment = namedtuple("Segment", ["x", "y", "speed", "direction", "width", "pressure"])

HEADER = b"reMarkable .lines file, version="
LAYER_DEF, LINE_DEF = 0x01010100, 0x05020200
fallback_readLines = None  # set by rmrender to rmrl's stock parser

# Empirical unit mappings (calibrated on real ballpoint-15 notebooks):
#   v6 per-point width u1 (~12-18 for ballpoint) -> px via /6
#   pressure/direction u1 0-255 -> float 0-1 / radians
WIDTH_DIV = 6.0
X_CENTER = 1404 / 2


class UnsupportedVersion(Exception):
    pass


def _walk_blocks(data):
    """Find the frontmatter end, then yield (flag, body) until EOF.

    Accepts only a walk that consumes the file exactly."""
    n = len(data)
    for start in range(80, 600):
        off = start
        blocks = []
        while off + 8 <= n:
            l, flag = struct.unpack_from("<II", data, off)
            if off + 8 + l > n or l > 10**7:
                break
            blocks.append((flag, off + 8, l))
            off += 8 + l
        if blocks and off == n:
            return blocks
    return None


def _term_positions(body, start, term, maxlen=5):
    return [i for i in range(start, min(start + maxlen, len(body))) if body[i] == term]


def _parse_tail(body, off, layer_id):
    """Parse the deterministic part after the id fields; None if invalid."""
    off += 2  # id_field_0 (u16)
    if off >= len(body) or body[off] != 0x54:
        return None
    off += 1
    (done,) = struct.unpack_from("<I", body, off)
    off += 4
    if done != 0:
        return None  # instantiated but unassigned line: no payload
    if body[off] != 0x6C:
        return None
    off += 1
    off += 4  # blklen
    if body[off : off + 2] != b"\x03\x14":
        return None
    off += 2
    (pen,) = struct.unpack_from("<I", body, off)
    off += 4
    if body[off] != 0x24:
        return None
    off += 1
    (color,) = struct.unpack_from("<I", body, off)
    off += 4
    if body[off : off + 5] != b"\x38\x00\x00\x00\x00":
        return None
    off += 5
    (brush,) = struct.unpack_from("<f", body, off)
    off += 4
    if body[off : off + 5] != b"\x44\x00\x00\x00\x00":
        return None
    off += 5
    if body[off] != 0x5C:
        return None
    off += 1
    (plen,) = struct.unpack_from("<I", body, off)
    off += 4
    if plen % 14 or off + plen > len(body):
        return None
    segments = []
    for _ in range(plen // 14):
        x, y = struct.unpack_from("<ff", body, off)
        speed, _p0, width, _p1, direction, pressure = body[off + 8 : off + 14]
        off += 14
        segments.append(
            Segment(
                x + X_CENTER,          # centered -> left origin
                y,                     # top origin already
                speed / 8.0,
                direction / 256.0 * 2 * 3.141592653589793,
                width / WIDTH_DIV,
                pressure / 255.0,
            )
        )
    if off + 3 > len(body) or body[off : off + 3] != b"\x6f\x00\x01":
        return None
    if not segments:
        return None
    return Stroke(pen=pen, color=color, unk1=0, width=brush, unk2=0, segments=segments), layer_id


def _parse_line(body):
    """Parse a line_def block. The three id fields are terminator-delimited
    (0x2f/0x3f/0x4f) but id bytes may themselves contain terminator values,
    so try all terminator positions and keep the interpretation whose tail
    validates through the 0x6f0001 trailer."""
    if not body or body[0] != 0x1F:
        return None
    for i in _term_positions(body, 1, 0x2F):
        layer_id = bytes(body[1:i])
        for j in _term_positions(body, i + 1, 0x3F):
            for k in _term_positions(body, j + 1, 0x4F):
                parsed = _parse_tail(body, k + 1, layer_id)
                if parsed is not None:
                    return parsed
    return None


def readLines(f):
    """rmrl-compatible readLines: v6 via this parser, older formats via
    the stock rmrl parser (set as fallback_readLines by the caller)."""
    data = f.read()
    if not data.startswith(HEADER[:32]):
        raise UnsupportedVersion("not a reMarkable lines file")
    if data[32:33] != b"6" and fallback_readLines is not None:
        f.seek(0)
        return fallback_readLines(f)
    blocks = _walk_blocks(data)
    if blocks is None:
        raise UnsupportedVersion("v6 block walk failed")

    layer_order = []          # layer ids in definition order
    layer_strokes = {}
    for flag, off, l in blocks:
        body = data[off : off + l]
        if flag == LAYER_DEF and l >= 3 and body[0] == 0x1F:
            idx = body.find(b"\x2f", 1, 6)
            if idx > 0:
                lid = bytes(body[1:idx])
                if lid not in layer_order:
                    layer_order.append(lid)
        elif flag == LINE_DEF:
            parsed = _parse_line(body)
            if parsed is not None:
                stroke, lid = parsed
                layer_strokes.setdefault(lid, []).append(stroke)

    result = [layer_strokes.pop(lid, []) for lid in layer_order]
    # lines referencing undeclared layers
    result.extend(layer_strokes.values())
    return (6, result)
