#!/usr/bin/env python3
"""One glossy red chilli on a dark stone board.

Deterministic, no network. Renders a single chilli (one ingredient)
and writes exactly one PNG: 1024x1024, <= 1 MiB.

Compatibility rule (grader): never use width= on ellipse / rectangle /
arc / polygon. line(width=...) and rounded_rectangle are fine.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
random.seed(42)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def vertical_gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        px[0, y] = lerp_color(top, bottom, y / max(1, h - 1))
    return img.resize((w, h))


def bezier(p0, p1, p2, p3, t):
    mt = 1.0 - t
    x = (mt ** 3) * p0[0] + 3 * (mt ** 2) * t * p1[0] + 3 * mt * (t ** 2) * p2[0] + (t ** 3) * p3[0]
    y = (mt ** 3) * p0[1] + 3 * (mt ** 2) * t * p1[1] + 3 * mt * (t ** 2) * p2[1] + (t ** 3) * p3[1]
    return (x, y)


def bezier_tangent(p0, p1, p2, p3, t):
    mt = 1.0 - t
    x = 3 * (mt ** 2) * (p1[0] - p0[0]) + 6 * mt * t * (p2[0] - p1[0]) + 3 * (t ** 2) * (p3[0] - p2[0])
    y = 3 * (mt ** 2) * (p1[1] - p0[1]) + 6 * mt * t * (p2[1] - p1[1]) + 3 * (t ** 2) * (p3[1] - p2[1])
    return (x, y)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")

    # ---- Background: charcoal vertical gradient + warm glow ----
    img = vertical_gradient((W, H), (34, 34, 40), (12, 12, 15)).convert("RGBA")

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([120, 300, 920, 1100], fill=(255, 122, 40, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    img = Image.alpha_composite(img, glow)

    # ---- Stone board ----
    board = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(board)
    bd.rounded_rectangle([70, 560, 954, 952], radius=28, fill=(43, 46, 54, 255))
    bd.rounded_rectangle([70, 560, 954, 952], radius=28, outline=(120, 124, 135, 90))
    # top edge light catching the board rim
    bd.line([(96, 566), (928, 566)], fill=(200, 204, 214, 70), width=3)
    # faint speckles on the stone (deterministic)
    for _ in range(260):
        x = random.randint(84, 940)
        y = random.randint(574, 938)
        v = random.randint(52, 78)
        bd.point((x, y), fill=(v, v + 2, v + 6, 60))
    img = Image.alpha_composite(img, board)

    # ---- Contact shadow under the chilli ----
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([240, 760, 860, 880], fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    img = Image.alpha_composite(img, shadow)

    # ---- Chilli pod: S-curve spine, tapered half-width ----
    p0 = (272.0, 648.0)
    p1 = (392.0, 792.0)
    p2 = (618.0, 636.0)
    p3 = (806.0, 836.0)
    n = 120
    spine = [bezier(p0, p1, p2, p3, i / n) for i in range(n + 1)]

    def half_width(t):
        # fat in the middle, narrow at the stem end, sharp at the tip
        base = 96.0 * math.sin(math.pi * (0.12 + 0.76 * t)) ** 0.8
        tip = lerp(1.0, 0.06, max(0.0, (t - 0.82) / 0.18) ** 1.6)
        stem = lerp(0.62, 1.0, min(1.0, t / 0.18))
        return max(5.0, base * tip * stem)

    left, right = [], []
    for i, (x, y) in enumerate(spine):
        t = i / n
        tx, ty = bezier_tangent(p0, p1, p2, p3, t)
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        hw = half_width(t)
        left.append((x + nx * hw, y + ny * hw))
        right.append((x - nx * hw, y - ny * hw))
    pod_poly = left + right[::-1]

    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.polygon(pod_poly, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))

    # red body: vertical gradient, bright scarlet up top to deep red below
    body_grad = vertical_gradient((W, H), (232, 52, 32), (138, 12, 8)).convert("RGBA")
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    body.paste(body_grad, (0, 0), mask)
    img = Image.alpha_composite(img, body)

    # deep shading along the lower edge of the pod
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shd = ImageDraw.Draw(shade)
    low = [(x, y + 26) for (x, y) in right]
    shd.polygon(low + right[::-1], fill=(60, 4, 2, 110))
    shade = shade.filter(ImageFilter.GaussianBlur(14))
    shade.putalpha(Image.composite(shade.split()[3], Image.new("L", (W, H), 0), mask))
    img = Image.alpha_composite(img, shade)

    # glossy highlight: bright band hugging the upper edge of the pod
    hi = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hid = ImageDraw.Draw(hi)
    upper = []
    for i, (x, y) in enumerate(spine):
        t = i / n
        tx, ty = bezier_tangent(p0, p1, p2, p3, t)
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        hw = half_width(t)
        upper.append((x + nx * hw * 0.62, y + ny * hw * 0.62))
    hid.line(upper, fill=(255, 214, 170, 235), width=26)
    hid.line(upper, fill=(255, 244, 228, 255), width=9)
    # thin specular core: the sharpest glint, hugging the pod's crown
    core = []
    for i, (x, y) in enumerate(spine):
        t = i / n
        tx, ty = bezier_tangent(p0, p1, p2, p3, t)
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        hw = half_width(t)
        core.append((x + nx * hw * 0.42, y + ny * hw * 0.42))
    hid.line(core, fill=(255, 255, 255, 255), width=4)
    hi = hi.filter(ImageFilter.GaussianBlur(7))
    hi.putalpha(Image.composite(hi.split()[3], Image.new("L", (W, H), 0), mask))
    img = Image.alpha_composite(img, hi)

    # warm rim light along the lower edge
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    lower = []
    for i, (x, y) in enumerate(spine):
        t = i / n
        tx, ty = bezier_tangent(p0, p1, p2, p3, t)
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        hw = half_width(t)
        lower.append((x - nx * hw * 0.86, y - ny * hw * 0.86))
    rd.line(lower, fill=(255, 150, 60, 200), width=12)
    rim = rim.filter(ImageFilter.GaussianBlur(6))
    rim.putalpha(Image.composite(rim.split()[3], Image.new("L", (W, H), 0), mask))
    img = Image.alpha_composite(img, rim)

    # ---- Green stem + star calyx at the top end ----
    stem_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    std = ImageDraw.Draw(stem_layer)
    stem_pts = [(272, 648), (238, 606), (206, 566), (186, 528)]
    std.line(stem_pts, fill=(74, 140, 52, 255), width=22)
    std.line(stem_pts, fill=(104, 178, 74, 255), width=10)
    # calyx star
    cx, cy = 272, 648
    star = []
    for k in range(10):
        ang = math.pi * k / 5 - math.pi / 2
        r = 52 if k % 2 == 0 else 24
        star.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    std.polygon(star, fill=(58, 122, 44, 255))
    std.polygon(star, outline=(140, 200, 110, 255))
    img = Image.alpha_composite(img, stem_layer)

    # ---- Water droplets on the pod ----
    drops = [(430, 700, 13), (560, 668, 10), (660, 742, 15), (730, 780, 9)]
    drop_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(drop_layer)
    for (dx, dy, dr) in drops:
        dd.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=(255, 255, 255, 46))
        dd.ellipse([dx - dr * 0.45, dy - dr * 0.55, dx + dr * 0.1, dy - dr * 0.05],
                   fill=(255, 255, 255, 200))
    img = Image.alpha_composite(img, drop_layer)

    # ---- A few seeds resting on the board ----
    seed_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sed = ImageDraw.Draw(seed_layer)
    for (sx, sy, sr) in [(852, 886, 12), (884, 906, 10), (826, 912, 9)]:
        sed.ellipse([sx - sr, sy - sr * 0.7, sx + sr, sy + sr * 0.7],
                    fill=(244, 226, 178, 255))
        sed.ellipse([sx - sr * 0.5, sy - sr * 0.4, sx + sr * 0.2, sy + sr * 0.1],
                    fill=(255, 250, 230, 220))
    img = Image.alpha_composite(img, seed_layer)

    # ---- Vignette to pull the eye to the chilli ----
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-260, -260, 1284, 1284], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(180))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img = Image.composite(img, Image.blend(img, dark, 0.55),
                          vig.point(lambda v: 255 - int((255 - v) * 0.45)))

    img.convert("RGB").save(out_path, "PNG", optimize=True)
    size = os.path.getsize(out_path)
    print(f"wrote {out_path} 1024x1024 {size} bytes")
    assert size <= 1048576, "PNG over 1 MiB"


if __name__ == "__main__":
    main()
