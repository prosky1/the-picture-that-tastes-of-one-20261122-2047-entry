#!/usr/bin/env python3
"""One glistening lemon slice, drawn fresh with PIL.

A single lemon wheel on a dark slate background, lit warmly from the
top-left: golden rind, pale pith, juicy translucent segments full of
vesicles, and beads of juice catching the light. Deterministic, no
network, no input files. Writes /output/entry.png (1024x1024).
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
SS = 2  # supersample factor for smooth edges
W = SIZE * SS
CX, CY = W // 2, W // 2 - 10 * SS
R_OUT = 385 * SS          # outer rind edge
R_RIND = 352 * SS         # rind / pith boundary
R_PITH = 330 * SS         # pith / flesh boundary
R_CORE = 34 * SS          # central core
N_SEG = 10

rng = random.Random(20261123)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def radial_bg():
    """Dark green-slate background, softly lit behind the lemon."""
    img = Image.new("RGB", (W, W), (10, 16, 12))
    px = img.load()
    cx0, cy0 = W * 0.42, W * 0.38
    for y in range(0, W, 2):
        for x in range(0, W, 2):
            d = math.hypot(x - cx0, y - cy0) / (W * 0.62)
            t = min(1.0, d)
            c = lerp((52, 66, 46), (8, 13, 10), t * t)
            px[x, y] = c
            px[x + 1, y] = c
            px[x, y + 1] = c
            px[x + 1, y + 1] = c
    return img


def soft_shadow(base):
    """Soft elliptical shadow under the wheel, lower right."""
    layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([CX - R_OUT * 0.98, CY + R_OUT * 0.72,
               CX + R_OUT * 1.02, CY + R_OUT * 1.06],
              fill=(0, 0, 0, 150))
    layer = layer.filter(ImageFilter.GaussianBlur(26 * SS))
    base.alpha_composite(layer)


def draw_rind(draw):
    """Golden rind: deep gold at the rim, bright yellow toward the pith."""
    steps = 60
    for i in range(steps):
        t = i / steps
        r0 = R_OUT - (R_OUT - R_RIND) * t
        r1 = R_OUT - (R_OUT - R_RIND) * (i + 1) / steps
        # warm light from the top-left brightens the upper rim
        c = lerp((176, 118, 8), (248, 205, 40), t)
        draw.ellipse([CX - r0, CY - r0, CX + r0, CY + r0],
                     outline=c, width=max(2, int((r0 - r1) + 2)))


def draw_pith(draw):
    # pale pith fills the whole band between rind and flesh
    draw.ellipse([CX - R_RIND, CY - R_RIND, CX + R_RIND, CY + R_RIND],
                 fill=(250, 246, 214))
    draw.ellipse([CX - R_RIND, CY - R_RIND, CX + R_RIND, CY + R_RIND],
                 outline=(232, 222, 170), width=3 * SS)
    draw.ellipse([CX - R_PITH, CY - R_PITH, CX + R_PITH, CY + R_PITH],
                 outline=(226, 214, 160), width=3 * SS)


def segment_flesh(draw):
    """Juicy flesh: each wedge gets its own radial pale-to-gold gradient."""
    flesh = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    fp = flesh.load()
    for y in range(CY - R_PITH, CY + R_PITH):
        for x in range(CX - R_PITH, CX + R_PITH):
            dx, dy = x - CX, y - CY
            r = math.hypot(dx, dy)
            if r > R_PITH - 2 * SS or r < R_CORE:
                continue
            ang = math.degrees(math.atan2(dy, dx)) % 360.0
            seg = int(ang // (360.0 / N_SEG))
            within = (ang % (360.0 / N_SEG)) / (360.0 / N_SEG)
            # gentle crease near each membrane, never muddy
            edge = min(within, 1.0 - within) * 2.0
            shade = 0.93 + 0.07 * min(1.0, edge * 3.0)
            # pale near the core, saturated gold toward the rim
            t = (r - R_CORE) / (R_PITH - R_CORE)
            base = lerp((255, 244, 170), (250, 196, 30), t)
            # slight per-segment hue jitter so wedges read individually
            jit = (seg * 37 % 11 - 5) / 255.0
            col = tuple(max(0, min(255, int(c * shade + jit * 255)))
                        for c in base)
            fp[x, y] = col + (255,)
    return flesh


def draw_membranes(draw):
    """White membranes radiating from the core to the pith."""
    for i in range(N_SEG):
        a = math.radians(i * 360.0 / N_SEG - 90)
        x1 = CX + int(math.cos(a) * (R_CORE + 4 * SS))
        y1 = CY + int(math.sin(a) * (R_CORE + 4 * SS))
        x2 = CX + int(math.cos(a) * (R_PITH - 3 * SS))
        y2 = CY + int(math.sin(a) * (R_PITH - 3 * SS))
        draw.line([x1, y1, x2, y2], fill=(252, 250, 226), width=5 * SS)
        draw.line([x1, y1, x2, y2], fill=(255, 255, 244), width=2 * SS)


def draw_core(draw):
    draw.ellipse([CX - R_CORE, CY - R_CORE, CX + R_CORE, CY + R_CORE],
                 fill=(250, 240, 190), outline=(240, 224, 150),
                 width=3 * SS)
    draw.ellipse([CX - R_CORE // 2, CY - R_CORE // 2,
                  CX + R_CORE // 2, CY + R_CORE // 2],
                 fill=(245, 222, 120))


def draw_vesicles(draw):
    """Juice vesicles: short pale dashes fanning out inside each wedge."""
    for seg in range(N_SEG):
        a0 = math.radians(seg * 360.0 / N_SEG - 90)
        for _ in range(30):
            rr = rng.uniform(R_CORE + 60 * SS, R_PITH - 14 * SS)
            aa = a0 + rng.uniform(0.05, (360.0 / N_SEG - 0.05)
                                  * math.pi / 180.0)
            # slight angular wobble so vesicles feel organic, not ruled
            aa += rng.uniform(-0.03, 0.03)
            x = CX + rr * math.cos(aa)
            y = CY + rr * math.sin(aa)
            ln = rng.uniform(8, 16) * SS
            # dash runs outward from the core
            ux, uy = math.cos(aa), math.sin(aa)
            col = (255, 253, 225, rng.randint(200, 235))
            draw.line([x - ux * ln / 2, y - uy * ln / 2,
                       x + ux * ln / 2, y + uy * ln / 2],
                      fill=col, width=2 * SS)


def gloss(base):
    """Warm gloss: big soft highlight top-left, small specular beads."""
    layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    gx, gy = CX - R_OUT * 0.42, CY - R_OUT * 0.46
    for r, alpha in ((170, 40), (120, 64), (75, 100), (40, 140)):
        d.ellipse([gx - r * SS, gy - r * SS * 0.62,
                   gx + r * SS, gy + r * SS * 0.62],
                  fill=(255, 250, 220, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(18 * SS))
    base.alpha_composite(layer)
    # bright crescent on the rind itself, top-left, where the light hits
    cres = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    dc = ImageDraw.Draw(cres)
    dc.arc([CX - R_OUT, CY - R_OUT, CX + R_OUT, CY + R_OUT],
           start=185, end=295, fill=(255, 246, 200, 150), width=26 * SS)
    cres = cres.filter(ImageFilter.GaussianBlur(10 * SS))
    base.alpha_composite(cres)


def droplets(base):
    """Beads of juice on the flesh and scattered on the dark table."""
    layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # on the flesh, near the rim
    for _ in range(14):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(R_PITH * 0.55, R_PITH * 0.92)
        x = CX + rr * math.cos(a)
        y = CY + rr * math.sin(a)
        r = rng.uniform(5, 11) * SS
        d.ellipse([x - r, y - r * 0.85, x + r, y + r * 0.85],
                  fill=(255, 246, 180, 210), outline=(255, 255, 235, 255),
                  width=2 * SS)
        d.ellipse([x - r * 0.45, y - r * 0.55, x + r * 0.1, y - r * 0.05],
                  fill=(255, 255, 255, 235))
    # on the table around the wheel, clustered close to the rim
    for _ in range(9):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(R_OUT * 1.05, R_OUT * 1.22)
        x = CX + rr * math.cos(a)
        y = CY + rr * math.sin(a)
        if y < 40 * SS or y > W - 40 * SS:
            continue
        r = rng.uniform(4, 12) * SS
        d.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8],
                  fill=(240, 214, 90, 190), outline=(255, 244, 190, 230),
                  width=2 * SS)
        d.ellipse([x - r * 0.4, y - r * 0.5, x + r * 0.15, y - r * 0.05],
                  fill=(255, 255, 240, 220))
    base.alpha_composite(layer)


def main():
    img = radial_bg().convert("RGBA")
    soft_shadow(img)
    ov = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    draw_rind(d)
    draw_pith(d)
    flesh = segment_flesh(d)
    ov.alpha_composite(flesh)
    d = ImageDraw.Draw(ov)
    draw_membranes(d)
    draw_core(d)
    draw_vesicles(d)
    img.alpha_composite(ov)
    gloss(img)
    droplets(img)
    img = img.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    out = os.environ.get("OUTPUT_PATH", "/output/entry.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print("wrote", out, img.size,
          os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
