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
LAYER_DEF, LINE_DEF, HIGHLIGHT_DEF = 0x01010100, 0x05020200, 0x03010100
HIGHLIGHT_PEN = 18  # rmrl PEN_MAPPING: highlighter
# text-highlight colour ids seen in the wild -> palette index
HIGHLIGHT_COLORS = {3: 3, 9: 5}  # 3 yellow, 9 pink
HIGHLIGHT_H_FACTOR = 1.0  # band height relative to the recorded line height
# Where the band sits relative to the recorded y, as a fraction of the line
# height. Measured against PDF text boxes on documents with 33 px and 104 px
# line heights: 0.413 and 0.483, i.e. y is essentially the band's top edge.
HIGHLIGHT_ANCHOR = 0.45
fallback_readLines = None  # set by rmrender to rmrl's stock parser

# Empirical unit mappings (calibrated on real ballpoint-15 notebooks):
#   v6 per-point width u1 (~12-18 for ballpoint) -> px via /6
#   pressure/direction u1 0-255 -> float 0-1 / radians
WIDTH_DIV = 6.0
SCREEN_W, SCREEN_H = 1404, 1872
DPI_PER_PT = 226 / 72  # device pixels per PDF point

# Coordinate frame applied to parsed points, set per document by the caller.
# Notebooks are already in screen pixels (x centred, y from the top). Imported
# PDFs are in page points x DPI_PER_PT, so they need the device's best-fit
# scale and the resulting letterbox offsets.
SCALE = 1.0
X_CENTER = SCREEN_W / 2
Y_OFFSET = 0.0


def set_notebook_frame():
    """Coordinates are already screen pixels."""
    global SCALE, X_CENTER, Y_OFFSET
    SCALE, X_CENTER, Y_OFFSET = 1.0, SCREEN_W / 2, 0.0


def set_pdf_frame(page_w_pt, page_h_pt):
    """Frame for annotations on an imported PDF page of the given size."""
    global SCALE, X_CENTER, Y_OFFSET
    w, h = page_w_pt * DPI_PER_PT, page_h_pt * DPI_PER_PT
    if w > h:  # the device shows a landscape page rotated; fit the short side
        w, h = h, w
    SCALE = min(SCREEN_W / w, SCREEN_H / h) if w and h else 1.0
    X_CENTER = SCREEN_W / 2
    # measured against rmapi's own annotated export: the page top aligns with
    # the canvas top, it is not letterboxed vertically
    Y_OFFSET = 0.0


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
    # 0x38 and 0x44 are field tags followed by four bytes that are NOT always
    # zero (they vary per pen), so only the tag itself may be checked
    if body[off] != 0x38:
        return None
    off += 5
    (brush,) = struct.unpack_from("<f", body, off)
    off += 4
    if body[off] != 0x44:
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
                x * SCALE + X_CENTER,      # centred -> left origin
                y * SCALE + Y_OFFSET,      # page top -> canvas top
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


def _parse_highlight(body):
    """Parse a text-highlight block.

    Layout: the usual id header, then tagged fields - 0x44 colour, 0x5c the
    highlighted text - followed by four float64s (x, y, width, height) in the
    same space as strokes (x centred on the page, y from its top).

    The offset of that float run varies, and a run read 8 bytes early can also
    satisfy any plausible range test, so all candidates are scored against the
    width the highlighted text should occupy at that line height."""
    if not body or body[0] != 0x1F:
        return None

    color = None
    j = body.find(b"\x44", 16, 48)
    if j > 0:
        (color,) = struct.unpack_from("<I", body, j + 1)

    text_len = 0
    k = body.find(b"\x5c", 16, 64)
    if k > 0 and k + 5 < len(body):
        text_len = body[k + 5]

    cands = []
    for off in range(8, len(body) - 31):
        x, y, w, h = struct.unpack_from("<dddd", body, off)
        if not (
            abs(x) <= 1200.0
            and 0.0 < y <= 3000.0
            and 2.0 <= w <= 1400.0
            and 8.0 <= h <= 120.0
        ):
            continue
        # a highlighted run of n characters is about 0.5 * line height wide
        # per character; score the relative error against that
        expected = max(text_len, 1) * h * 0.5
        cands.append((abs(w - expected) / expected, x, y, w, h))
    if not cands:
        return None

    cands.sort()
    _, bx, by, bw, bh = cands[0]
    # a highlight spanning several lines stores one rect per line in the same
    # block; keep the others, which share the line height but sit at a
    # different y. Bogus reads (a run decoded a few bytes off) do not.
    rects = [(bx, by, bw, bh)]
    for _, x, y, w, h in cands[1:]:
        if abs(h - bh) > 0.02 * bh or w > bw * 1.05:
            continue
        if all(abs(y - ry) > bh * 0.5 or abs(x - rx) > 1.0 for rx, ry, _, _ in rects):
            rects.append((x, y, w, h))

    out = []
    for x, y, w, h in rects:
        mid = (y + HIGHLIGHT_ANCHOR * h) * SCALE + Y_OFFSET
        out.append(
            Stroke(
                pen=HIGHLIGHT_PEN,
                color=HIGHLIGHT_COLORS.get(color, 3),
                unk1=0,
                width=h * SCALE * HIGHLIGHT_H_FACTOR,
                unk2=0,
                segments=[
                    Segment(x * SCALE + X_CENTER, mid, 0.0, 0.0, h * SCALE, 1.0),
                    Segment((x + w) * SCALE + X_CENTER, mid, 0.0, 0.0, h * SCALE, 1.0),
                ],
            )
        )
    return out


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
    highlights = []
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
        elif flag == HIGHLIGHT_DEF:
            hl = _parse_highlight(body)
            if hl:
                highlights.extend(hl)

    result = [layer_strokes.pop(lid, []) for lid in layer_order]
    # lines referencing undeclared layers
    result.extend(layer_strokes.values())
    # highlights go first so ink is drawn over the translucent bands
    if highlights:
        result.insert(0, highlights)
    return (6, result)
