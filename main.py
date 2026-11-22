"""One ingredient, one picture: a single glistening lemon slice.

main.py (Python 3.13, Pillow only, no network, deterministic) draws a
1024x1024 PNG of one fresh lemon slice -- rind, pith, juicy segments,
droplets and gloss -- on a dark slate backdrop, and writes it to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
CX, CY = 512, 500          # slice centre (slightly above middle)
R = 380                    # outer radius of the slice
rng = random.Random(20261123)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def radial_bg(size):
    """Dark green-charcoal backdrop, brighter behind the slice."""
    img = Image.new("RGB", (size, size))
    px = img.load()
    cx, cy = size // 2, size // 2 - 40
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - cx, y - cy) / (size * 0.72)
            t = min(1.0, d)
            # warm dark centre -> near-black green edges
            px[x, y] = lerp((52, 66, 46), (10, 14, 11), t)
    return img


def draw_soft_shadow(base):
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.ellipse([CX - 360, CY + 300, CX + 360, CY + 395], fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    base.alpha_composite(sh)


def lemon_slice(base):
    """Draw the slice on its own layer so we can tilt it slightly."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # NOTE: PIL ImageDraw REPLACES pixels instead of blending, so every
    # semi-transparent detail (dimples, vesicles, droplets) must live on
    # a separate overlay that is alpha-composited at the end -- drawing
    # them straight on `layer` would punch dark see-through holes.
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)

    # --- outer rind: deep yellow ring with a bumpy edge -------------
    for r, col in ((R, (176, 138, 8)), (R - 14, (214, 176, 16)),
                   (R - 30, (240, 205, 32))):
        d.ellipse([CX - r, CY - r, CX + r, CY + r], fill=col + (255,))
    # rind dimples: faint warm pits, never dark (dark reads as dirt)
    for _ in range(200):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(R - 30, R - 2)
        x, y = CX + rr * math.cos(a), CY + rr * math.sin(a)
        s = rng.uniform(1.5, 4)
        od.ellipse([x - s, y - s, x + s, y + s],
                   fill=(206, 164, 20, 55))

    # --- white pith ring -------------------------------------------
    d.ellipse([CX - (R - 34), CY - (R - 34), CX + (R - 34), CY + (R - 34)],
              fill=(250, 246, 224, 255))
    d.ellipse([CX - (R - 52), CY - (R - 52), CX + (R - 52), CY + (R - 52)],
              fill=(255, 244, 130, 255))

    # --- flesh: pale yellow disc, deeper gold toward the rim --------
    flesh_r = R - 56
    flesh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(flesh)
    for rr in range(flesh_r, 0, -6):
        t = rr / flesh_r  # 1 at rim, 0 at centre
        fd.ellipse([CX - rr, CY - rr, CX + rr, CY + rr],
                   fill=lerp((255, 244, 140), (250, 214, 60), t) + (255,))
    layer.alpha_composite(flesh)
    d = ImageDraw.Draw(layer)

    # --- segments: 11 wedges split by pale membranes ---------------
    n = 11
    for i in range(n):
        a0 = 2 * math.pi * i / n + 0.06
        a1 = 2 * math.pi * (i + 1) / n - 0.06
        # wedge slightly deeper yellow at its outer edge
        d.pieslice([CX - flesh_r + 6, CY - flesh_r + 6,
                    CX + flesh_r - 6, CY + flesh_r - 6],
                   math.degrees(a0), math.degrees(a1),
                   fill=(252, 224, 62, 255))
        # juice vesicles: short warm-white radial strokes in the wedge
        for _ in range(40):
            ang = rng.uniform(a0 + 0.08, a1 - 0.08)
            rr = rng.uniform(28, flesh_r - 26)
            x0 = CX + rr * math.cos(ang)
            y0 = CY + rr * math.sin(ang)
            ln = rng.uniform(6, 13)
            x1 = x0 + ln * math.cos(ang)
            y1 = y0 + ln * math.sin(ang)
            od.line([x0, y0, x1, y1], fill=(255, 252, 205, 170), width=2)
        # membrane: pale line from centre to rim
        am = 2 * math.pi * (i + 1) / n
        d.line([CX + 14 * math.cos(am), CY + 14 * math.sin(am),
                CX + (flesh_r - 4) * math.cos(am),
                CY + (flesh_r - 4) * math.sin(am)],
               fill=(255, 252, 225, 255), width=9)

    # --- centre star -------------------------------------------------
    d.ellipse([CX - 26, CY - 26, CX + 26, CY + 26],
              fill=(255, 252, 225, 255))
    d.ellipse([CX - 15, CY - 15, CX + 15, CY + 15],
              fill=(240, 222, 90, 255))

    # --- gloss: big soft highlight upper-left on the flesh ----------
    gloss = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(gloss)
    g.ellipse([CX - 310, CY - 340, CX + 60, CY - 40],
              fill=(255, 255, 255, 95))
    g.ellipse([CX - 220, CY - 290, CX - 30, CY - 140],
              fill=(255, 255, 255, 120))
    gloss = gloss.filter(ImageFilter.GaussianBlur(26))
    layer.alpha_composite(gloss)

    # --- juice droplets: pale-yellow translucent beads ---------------
    for _ in range(42):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(R - 40, R + 26)
        x, y = CX + rr * math.cos(a), CY + rr * math.sin(a)
        s = rng.uniform(4, 11)
        od.ellipse([x - s, y - s * 0.8, x + s, y + s * 0.8],
                   fill=(255, 246, 150, 170), outline=(255, 255, 230, 230))
        od.ellipse([x - s * 0.45, y - s * 0.5, x + s * 0.1, y - s * 0.05],
                   fill=(255, 255, 255, 235))
    # a few beads resting on the flesh itself
    for _ in range(10):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(60, flesh_r - 40)
        x, y = CX + rr * math.cos(a), CY + rr * math.sin(a)
        s = rng.uniform(5, 9)
        od.ellipse([x - s, y - s * 0.8, x + s, y + s * 0.8],
                   fill=(255, 250, 190, 150), outline=(255, 255, 240, 200))
        od.ellipse([x - s * 0.4, y - s * 0.45, x + s * 0.15, y - s * 0.05],
                   fill=(255, 255, 255, 230))

    # warm rim light: a soft golden arc on the lower-right rind
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.arc([CX - R - 6, CY - R - 6, CX + R + 6, CY + R + 6],
           start=15, end=105, fill=(255, 226, 110, 130), width=16)
    rim = rim.filter(ImageFilter.GaussianBlur(10))
    layer.alpha_composite(rim)

    layer.alpha_composite(ov)
    return layer


def droplets_around(base):
    """A few juice drops and a splash arc flying off the slice."""
    d = ImageDraw.Draw(base)
    for (x, y, s) in [(150, 830, 12), (205, 885, 8), (880, 850, 13),
                      (845, 905, 7), (905, 790, 6), (120, 760, 6)]:
        d.ellipse([x - s, y - s, x + s, y + s],
                  fill=(250, 230, 90, 255), outline=(255, 255, 220, 255))
        d.ellipse([x - s * 0.4, y - s * 0.45, x + s * 0.15, y - s * 0.1],
                  fill=(255, 255, 255, 235))


def vignette(base):
    vg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(vg)
    d.rectangle([0, 0, W, H], outline=(0, 0, 0, 170), width=90)
    vg = vg.filter(ImageFilter.GaussianBlur(60))
    base.alpha_composite(vg)


def main():
    img = radial_bg(W).convert("RGBA")
    draw_soft_shadow(img)
    layer = lemon_slice(img)
    layer = layer.rotate(-8, center=(CX, CY), resample=Image.BICUBIC)
    img.alpha_composite(layer)
    droplets_around(img)
    vignette(img)

    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(outdir, exist_ok=True)
        path = os.path.join(outdir, "entry.png")
        img.convert("RGB").save(path, "PNG", optimize=True)
    except OSError:
        os.makedirs("output", exist_ok=True)
        path = os.path.join("output", "entry.png")
        img.convert("RGB").save(path, "PNG", optimize=True)
    print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
