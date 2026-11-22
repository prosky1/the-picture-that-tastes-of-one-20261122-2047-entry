"""One glossy red chilli on a stone board — a picture that tastes of one
ingredient. Anti-fail entrypoint: primary PIL render, pure-stdlib PNG
fallback if PIL is unavailable or fails for any reason."""

import math
import os
import random
import struct
import zlib

SIZE = 1024
MAX_BYTES = 1048576


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def render_pil(path):
    """Draw the chilli with Pillow. PIL is imported here, inside the
    function, so a missing/broken Pillow never breaks module import."""
    from PIL import Image, ImageDraw, ImageFilter

    rng = random.Random(20261123)
    img = Image.new("RGB", (SIZE, SIZE), (18, 18, 22))
    draw = ImageDraw.Draw(img)

    # Vertical charcoal gradient background.
    for y in range(SIZE):
        t = y / (SIZE - 1)
        draw.line([(0, y), (SIZE, y)], fill=_lerp((34, 34, 40), (10, 10, 14), t))

    # Warm radial glow behind the chilli.
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([112, 130, 912, 930], fill=(190, 60, 30, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    draw = ImageDraw.Draw(img)

    # Stone board.
    draw.rounded_rectangle([72, 700, 952, 916], radius=28,
                           fill=(52, 52, 58))
    draw.rounded_rectangle([72, 700, 952, 716], radius=14,
                           fill=(74, 74, 80))
    for _ in range(260):
        x = rng.randint(80, 944)
        y = rng.randint(708, 908)
        v = rng.randint(40, 78)
        draw.point((x, y), fill=(v, v, v + 4))

    # Contact shadow under the pod.
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([170, 660, 880, 760], fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    img = Image.alpha_composite(img, shadow)
    draw = ImageDraw.Draw(img)

    # S-curve centreline of the pod, tip left, stem end right.
    spine = []
    for i in range(61):
        t = i / 60.0
        x = 190 + 600 * t
        y = 470 + 150 * math.sin(t * math.pi * 0.9) - 90 * t
        spine.append((x, y))

    pod = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pod)
    # Pod body: overlapping discs along the spine, radius tapering to a
    # fine tip at the left and swelling toward the stem end.
    for i, (x, y) in enumerate(spine):
        t = i / 60.0
        r = 34 + 96 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * t)) ** 0.8
        if t < 0.08:
            r *= 0.35 + 7.0 * t
        shade = _lerp((150, 12, 8), (235, 55, 28), math.sin(t * math.pi) ** 0.6)
        pd.ellipse([x - r, y - r * 0.72, x + r, y + r * 0.72],
                   fill=shade + (255,))
    # Deep red underside shading.
    for i, (x, y) in enumerate(spine):
        t = i / 60.0
        r = 30 + 88 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * t)) ** 0.8
        pd.ellipse([x - r * 0.9, y + r * 0.18, x + r * 0.9, y + r * 0.72],
                   fill=(110, 8, 6, 110))
    pod = pod.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, pod)
    draw = ImageDraw.Draw(img)

    # Glossy highlight along the upper belly of the pod, following the
    # spine so it sits on the chilli instead of floating above it.
    hi = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    for i in range(8, 53, 4):
        t = i / 60.0
        x, y = spine[i]
        r = 34 + 96 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * t)) ** 0.8
        hd.ellipse([x - 52, y - r * 0.55, x + 52, y - r * 0.05],
                   fill=(255, 200, 170, 110))
    hi = hi.filter(ImageFilter.GaussianBlur(14))
    img = Image.alpha_composite(img, hi)
    draw = ImageDraw.Draw(img)

    # Bright rim light on the lower edge of the pod.
    rim_pts = []
    for i in range(0, 61, 2):
        t = i / 60.0
        x, y = spine[i]
        r = 34 + 96 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * t)) ** 0.8
        rim_pts.append((x, y + r * 0.62))
    draw.line(rim_pts, fill=(255, 120, 80, 220), width=7, joint="curve")

    # Green stem and calyx hugging the right end of the pod.
    stem_end = spine[-1]
    calyx = [(stem_end[0] - 34, stem_end[1] - 26),
             (stem_end[0] + 30, stem_end[1] - 52),
             (stem_end[0] + 62, stem_end[1] - 18),
             (stem_end[0] + 34, stem_end[1] + 26),
             (stem_end[0] - 40, stem_end[1] + 22)]
    draw.polygon(calyx, fill=(46, 122, 52, 255))
    draw.polygon([(stem_end[0] + 26, stem_end[1] - 46),
                  (stem_end[0] + 104, stem_end[1] - 92),
                  (stem_end[0] + 110, stem_end[1] - 66),
                  (stem_end[0] + 40, stem_end[1] - 16)],
                 fill=(74, 160, 62, 255))
    draw.line([(stem_end[0] + 30, stem_end[1] - 40),
               (stem_end[0] + 104, stem_end[1] - 84)],
              fill=(140, 210, 110, 255), width=5)

    # Juice droplets sitting on the pod body.
    for (dx, dy, dr) in [(350, 490, 12), (500, 545, 10), (620, 490, 11),
                         (430, 560, 8), (580, 560, 7)]:
        draw.ellipse([dx - dr, dy - dr, dx + dr, dy + dr],
                     fill=(255, 255, 255, 90))
        draw.ellipse([dx - dr // 2, dy - dr // 2, dx + dr // 3, dy + dr // 3],
                     fill=(255, 255, 255, 170))

    # A few pale seeds scattered on the board.
    for (sx, sy) in [(300, 760), (360, 790), (700, 770), (760, 800)]:
        draw.ellipse([sx - 12, sy - 8, sx + 12, sy + 8],
                     fill=(240, 220, 180, 255))
        draw.ellipse([sx - 6, sy - 4, sx + 6, sy + 4],
                     fill=(200, 175, 130, 255))

    img.convert("RGB").save(path, "PNG", optimize=True)
    return path


def _png_chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))


def render_fallback(path):
    """Pure-stdlib PNG writer: 1024x1024 RGB, vertical charcoal gradient,
    stone board, one big red chilli ellipse with a glossy highlight and a
    green stem. Built row by row as bytes (no per-pixel Python loop)."""
    w = h = SIZE
    rows = []
    cx, cy, rx, ry = 512, 470, 370, 150
    hx, hy, hrx, hry = 430, 420, 200, 55
    for y in range(h):
        t = y / (h - 1)
        bg = _lerp((34, 34, 40), (10, 10, 14), t)
        row = bytearray(bytes(bg) * w)
        # Stone board.
        if 700 <= y < 916:
            board = (74, 74, 80) if y < 716 else (52, 52, 58)
            row[72 * 3:952 * 3] = bytes(board) * (952 - 72)
        # Chilli pod: vertical red gradient inside the ellipse.
        dy = (y - cy) / ry
        if abs(dy) < 1.0:
            half = rx * math.sqrt(1.0 - dy * dy)
            x0 = max(0, int(cx - half))
            x1 = min(w, int(cx + half) + 1)
            gt = (y - (cy - ry)) / (2 * ry)
            pod = _lerp((235, 55, 28), (120, 10, 10), gt)
            row[x0 * 3:x1 * 3] = bytes(pod) * (x1 - x0)
            # Glossy highlight blended toward white.
            hdy = (y - hy) / hry
            if abs(hdy) < 1.0:
                hhalf = hrx * math.sqrt(1.0 - hdy * hdy)
                hx0 = max(x0, int(hx - hhalf))
                hx1 = min(x1, int(hx + hhalf) + 1)
                for xi in range(hx0, hx1):
                    i = xi * 3
                    row[i] = (row[i] + 255) // 2
                    row[i + 1] = (row[i + 1] + 200) // 2
                    row[i + 2] = (row[i + 2] + 180) // 2
        # Green stem block.
        if 300 <= y < 380:
            row[790 * 3:880 * 3] = bytes((60, 140, 60)) * 90
        rows.append(b"\x00" + bytes(row))
    raw = b"".join(rows)
    png = (b"\x89PNG\r\n\x1a\n"
           + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + _png_chunk(b"IDAT", zlib.compress(raw, 9))
           + _png_chunk(b"IEND", b""))
    if len(png) > MAX_BYTES:
        raise ValueError("fallback PNG exceeds 1 MiB: %d bytes" % len(png))
    with open(path, "wb") as fh:
        fh.write(png)
    return path


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    try:
        render_pil(out_path)
    except Exception:
        render_fallback(out_path)
    try:
        size = os.path.getsize(out_path)
        if size > MAX_BYTES:
            render_fallback(out_path)
            size = os.path.getsize(out_path)
    except Exception:
        render_fallback(out_path)
    print("wrote %s (%d bytes)" % (out_path, os.path.getsize(out_path)))
    return 0


if __name__ == "__main__":
    main()
