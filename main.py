#!/usr/bin/env python3
"""One glossy red chilli on a dark slate board.

Draws a single fresh red chilli pepper with a green stem, water
droplets and a glossy highlight, on a dark charcoal background.
Deterministic, no network, pure PIL.
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
PATH = os.path.join(OUT, "entry.png")

rng = random.Random(20261123)

img = Image.new("RGB", (W, H), (18, 20, 24))
d = ImageDraw.Draw(img, "RGBA")

# ---- dark slate backdrop with soft vignette glow behind the chilli ----
glow = Image.new("RGB", (W, H), (0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([180, 180, 844, 844], fill=(52, 40, 38))
glow = glow.filter(ImageFilter.GaussianBlur(90))
img = Image.blend(img, Image.blend(img, glow, 0.9), 0.55)
d = ImageDraw.Draw(img, "RGBA")

# ---- stone board: a dark rounded slab under the chilli ----
d.rounded_rectangle([110, 700, 914, 900], radius=46, fill=(38, 40, 46))
d.rounded_rectangle([110, 700, 914, 716], radius=20, fill=(58, 60, 68))
for _ in range(260):
    x = rng.randint(120, 900)
    y = rng.randint(712, 888)
    d.point((x, y), fill=(70 + rng.randint(0, 25), 72 + rng.randint(0, 25), 80))

# ---- chilli body: a smooth curved pod, drawn as stacked slices ----
# Centreline of the pod: a long, low S-curve lying just above the board.
def centre(t):
    x = 215 + 580 * t
    y = 585 - 105 * math.sin(t * math.pi * 0.85) + 35 * t * t
    return x, y

def width(t):
    # plump near the stem end, tapering gently to a curled tip
    return 165 * (1 - 0.45 * t) * (0.8 + 0.2 * math.sin(math.pi * min(1.0, t * 1.1)))

body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(body)
N = 220
for i in range(N):
    t = i / (N - 1)
    cx, cy = centre(t)
    w = width(t)
    # direction along the curve
    cx2, cy2 = centre(min(1.0, t + 0.01))
    dx, dy = cx2 - cx, cy2 - cy
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    # vertical gradient of red: bright top edge, deep belly
    shade = 0.72 + 0.28 * math.sin(math.pi * (0.15 + 0.7 * t))
    r = int(214 * shade)
    g = int(26 * shade + 14)
    b = int(18 * shade + 8)
    bd.line([(cx - nx * w, cy - ny * w), (cx + nx * w, cy + ny * w)],
            fill=(r, g, b, 255), width=9)
body = body.filter(ImageFilter.GaussianBlur(1.2))
img = Image.alpha_composite(img.convert("RGBA"), body)
d = ImageDraw.Draw(img, "RGBA")

# ---- glossy highlight along the upper edge of the pod ----
hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(hl)
for i in range(90):
    t = 0.08 + 0.55 * i / 89
    cx, cy = centre(t)
    cx2, cy2 = centre(min(1.0, t + 0.01))
    dx, dy = cx2 - cx, cy2 - cy
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    w = width(t)
    off = -w * 0.52
    a = int(190 * (1 - abs(t - 0.35) * 1.4))
    hd.line([(cx + nx * off - dx * 3, cy + ny * off - dy * 3),
             (cx + nx * off + dx * 3, cy + ny * off + dy * 3)],
            fill=(255, 205, 175, max(0, a)), width=26)
hl = hl.filter(ImageFilter.GaussianBlur(10))
img = Image.alpha_composite(img, hl)
d = ImageDraw.Draw(img, "RGBA")

# ---- warm rim light along the lower edge of the pod ----
rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd = ImageDraw.Draw(rim)
for i in range(90):
    t = 0.1 + 0.6 * i / 89
    cx, cy = centre(t)
    cx2, cy2 = centre(min(1.0, t + 0.01))
    dx, dy = cx2 - cx, cy2 - cy
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    w = width(t)
    off = w * 0.62
    a = int(90 * (1 - abs(t - 0.4) * 1.3))
    rd.line([(cx + nx * off - dx * 3, cy + ny * off - dy * 3),
             (cx + nx * off + dx * 3, cy + ny * off + dy * 3)],
            fill=(255, 110, 70, max(0, a)), width=16)
rim = rim.filter(ImageFilter.GaussianBlur(9))
img = Image.alpha_composite(img, rim)
d = ImageDraw.Draw(img, "RGBA")

# ---- soft contact shadow on the board under the pod ----
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(sh)
sd.ellipse([230, 640, 790, 716], fill=(0, 0, 0, 110))
sh = sh.filter(ImageFilter.GaussianBlur(18))
img = Image.alpha_composite(img, sh)
d = ImageDraw.Draw(img, "RGBA")

# ---- green stem ----
stem = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(stem)
td.line([(218, 585), (168, 470), (128, 396)], fill=(46, 128, 52, 255), width=24)
td.line([(218, 585), (168, 470), (128, 396)], fill=(96, 178, 80, 255), width=11)
# calyx star at the pod's shoulder
cx0, cy0 = 218, 585
for ang in range(0, 360, 72):
    a = math.radians(ang - 90)
    td.polygon([(cx0, cy0),
                (cx0 + 46 * math.cos(a - 0.22), cy0 + 46 * math.sin(a - 0.22)),
                (cx0 + 46 * math.cos(a + 0.22), cy0 + 46 * math.sin(a + 0.22))],
               fill=(52, 138, 58, 255))
td.ellipse([cx0 - 26, cy0 - 23, cx0 + 26, cy0 + 23], fill=(58, 150, 64, 255))
stem = stem.filter(ImageFilter.GaussianBlur(1.0))
img = Image.alpha_composite(img, stem)
d = ImageDraw.Draw(img, "RGBA")

# ---- water droplets on the pod: small, sparse, subtle ----
for _ in range(13):
    t = rng.uniform(0.12, 0.88)
    cx, cy = centre(t)
    w = width(t)
    off = rng.uniform(-0.5, 0.5) * w
    cx2, cy2 = centre(min(1.0, t + 0.01))
    dx, dy = cx2 - cx, cy2 - cy
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    px, py = cx + nx * off, cy + ny * off
    r = rng.uniform(3, 8)
    d.ellipse([px - r, py - r, px + r, py + r],
              fill=(255, 255, 255, 55), outline=(255, 255, 255, 120), width=1)
    d.ellipse([px - r * 0.45, py - r * 0.5, px - r * 0.05, py - r * 0.1],
              fill=(255, 255, 255, 160))

# ---- a few scattered chilli seeds on the board for appetite ----
for (sx, sy) in [(700, 780), (748, 812), (668, 826), (800, 770)]:
    d.ellipse([sx - 14, sy - 10, sx + 14, sy + 10], fill=(240, 214, 150, 255),
              outline=(196, 160, 96, 255), width=2)

os.makedirs(OUT, exist_ok=True)
img.convert("RGB").save(PATH, "PNG", optimize=True)
print("wrote", PATH)
