#!/usr/bin/env python3
"""One glossy red chilli on a dark stone board.

Fresh implementation, written from the design brief: a single red chilli
pod in a low S-curve, glossy highlight on the upper edge, warm rim light
on the belly, green stem with a star calyx, water droplets on the pod and
a few pale seeds on the board. Deterministic, no network, Python + Pillow.

Compatibility note (grader sandbox runs an older Pillow): NEVER pass
``width=`` to ellipse / rectangle / arc / polygon. ``rounded_rectangle``
and ``line(width=...)`` are fine on the grader.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
OUT_NAME = "entry.png"


def out_dir():
    return os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def spine_points():
    """Centre line of the pod: a low S-curve from left to right."""
    pts = []
    for i in range(121):
        t = i / 120.0
        x = 150 + 700 * t
        y = 470 + 58 * math.sin(t * math.pi * 1.15 - 0.35) - 46 * t
        pts.append((x, y))
    return pts


def pod_half_width(t):
    """Half-thickness of the pod along the spine (fat left, tapered tail)."""
    base = 118 * (1 - 0.42 * t) + 26 * math.sin(t * math.pi)
    return max(base, 26)


def pod_outline():
    """Outline polygon of the pod, built from spine + normals."""
    spine = spine_points()
    top, bottom = [], []
    for i, (x, y) in enumerate(spine):
        t = i / (len(spine) - 1)
        x0, y0 = spine[max(i - 1, 0)]
        x1, y1 = spine[min(i + 1, len(spine) - 1)]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        w = pod_half_width(t)
        top.append((x + nx * w, y + ny * w))
        bottom.append((x - nx * w, y - ny * w))
    return top + bottom[::-1], top, bottom


def vertical_gradient(size, top_color, bottom_color):
    grad = Image.new("RGB", (1, size[1]))
    px = grad.load()
    for y in range(size[1]):
        px[0, y] = lerp_color(top_color, bottom_color, y / max(size[1] - 1, 1))
    return grad.resize(size)


def clip_layer(layer, mask):
    """Keep only the part of an RGBA layer inside the L-mode mask."""
    alpha = Image.composite(layer.split()[3], Image.new("L", layer.size, 0), mask)
    layer.putalpha(alpha)
    return layer


def main():
    # ---- background: charcoal with a warm radial glow behind the pod ----
    bg = Image.new("RGB", (W, H), (14, 14, 17)).convert("RGBA")
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gld = ImageDraw.Draw(glow_layer)
    gld.ellipse([230, 180, 830, 780], fill=(120, 52, 24, 110))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(140))
    bg = Image.alpha_composite(bg, glow_layer)

    # ---- stone board: dark slate slab with a soft top edge ----
    board = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(board)
    bd.rounded_rectangle([110, 612, 914, 872], radius=42, fill=(52, 56, 62, 255))
    bd.rounded_rectangle([110, 612, 914, 676], radius=42, fill=(74, 79, 87, 255))
    bd.line([150, 624, 874, 624], fill=(110, 116, 126, 255), width=3)
    bg = Image.alpha_composite(bg, board)

    # ---- contact shadow under the pod ----
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([190, 585, 830, 692], fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    bg = Image.alpha_composite(bg, shadow)

    # ---- pod body: red gradient clipped by the pod mask ----
    outline, top_edge, bottom_edge = pod_outline()
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.polygon(outline, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))

    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    x0, x1 = int(min(xs)) - 4, int(max(xs)) + 4
    y0, y1 = int(min(ys)) - 4, int(max(ys)) + 4
    grad = vertical_gradient((x1 - x0, y1 - y0), (238, 74, 52), (122, 12, 10))
    pod = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pod.paste(grad, (x0, y0))
    pod.putalpha(mask)

    # belly shading: darker red low on the pod, clipped by the mask
    belly = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bld = ImageDraw.Draw(belly)
    bld.ellipse([180, 480, 850, 640], fill=(60, 3, 5, 130))
    belly = belly.filter(ImageFilter.GaussianBlur(30))
    pod = Image.alpha_composite(pod, clip_layer(belly, mask))

    # glossy highlight: bright band along the upper edge, clipped by mask
    gloss = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gld2 = ImageDraw.Draw(gloss)
    gld2.line(top_edge, fill=(255, 224, 196, 245), width=14)
    gld2.line([(x, y + 20) for x, y in top_edge],
              fill=(255, 158, 116, 150), width=30)
    gloss = gloss.filter(ImageFilter.GaussianBlur(6))
    pod = Image.alpha_composite(pod, clip_layer(gloss, mask))

    # warm rim light along the lower edge
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rmd = ImageDraw.Draw(rim)
    rmd.line(bottom_edge, fill=(255, 122, 52, 220), width=6)
    rim = rim.filter(ImageFilter.GaussianBlur(5))
    pod = Image.alpha_composite(pod, clip_layer(rim, mask))

    bg = Image.alpha_composite(bg, pod).convert("RGB")

    # ---- stem + star calyx at the left end of the pod ----
    fg = ImageDraw.Draw(bg)
    fg.line([168, 452, 128, 330], fill=(58, 148, 66), width=17)
    fg.line([168, 452, 128, 330], fill=(96, 196, 96), width=7)
    cx, cy = 168, 452
    star = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        r = 52 if k % 2 == 0 else 20
        star.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    fg.polygon(star, fill=(46, 130, 56))
    inner = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        r = 28 if k % 2 == 0 else 11
        inner.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    fg.polygon(inner, fill=(74, 168, 76))

    # ---- water droplets on the pod (plain filled ellipses, no width) ----
    drops = [
        (300, 430, 15, 11), (392, 402, 11, 8), (470, 442, 18, 13),
        (560, 408, 12, 9), (648, 448, 14, 10), (716, 420, 9, 7),
        (520, 470, 10, 7), (420, 478, 8, 6),
    ]
    for dx, dy, rx, ry in drops:
        fg.ellipse([dx - rx, dy - ry, dx + rx, dy + ry],
                   fill=(214, 232, 240))
        fg.ellipse([dx - rx * 0.45, dy - ry * 0.55,
                    dx + rx * 0.15, dy - ry * 0.05],
                   fill=(255, 255, 255))

    # ---- a few pale seeds scattered on the board ----
    seeds = [(640, 742, 13, 9, -18), (700, 762, 12, 8, 12),
             (758, 740, 11, 8, -8), (676, 800, 12, 8, 24)]
    for sx, sy, rx, ry, ang in seeds:
        seed = Image.new("RGBA", (rx * 2 + 8, ry * 2 + 8), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(seed)
        sdraw.ellipse([4, 4, 4 + rx * 2, 4 + ry * 2],
                      fill=(238, 214, 150, 255))
        sdraw.ellipse([4 + rx // 2, 4 + ry // 2,
                       4 + rx * 2 - rx // 2, 4 + ry * 2 - ry // 3],
                      fill=(250, 236, 196, 255))
        seed = seed.rotate(ang, resample=Image.BICUBIC, expand=False)
        bg.paste(seed, (sx - rx - 4, sy - ry - 4), seed)

    # ---- vignette: darken the corners slightly ----
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-220, -220, W + 220, H + 220], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(180))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.composite(bg, black, vig)

    # ---- write output ----
    os.makedirs(out_dir(), exist_ok=True)
    path = os.path.join(out_dir(), OUT_NAME)
    bg.save(path, format="PNG", optimize=True)
    print("wrote", path, bg.size, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
