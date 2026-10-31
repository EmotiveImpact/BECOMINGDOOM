#!/usr/bin/env python3
"""DOOM GRADE: the locked image grade for Becoming Doom.

Darker, higher contrast, neutral blacks, red kept as the only colour accent.
  - kills blue and teal casts (cool hues lose almost all saturation)
  - protects reds fully and skin tones mostly (so Black skin never goes grey)
  - crushes the black point and pulls the mids down
  - S-curve contrast, then a heavy vignette into pure black
  - fine grain to stop banding in the blacks

Usage: python3 tools/doom_grade.py in.png out.png [--strength 1.0]
"""
import sys, argparse
import numpy as np
from PIL import Image


def rgb_to_hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rm = m & (mx == r); gm = m & (mx == g) & ~rm; bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    return h * 60.0, np.where(mx > 0, d / np.maximum(mx, 1e-6), 0), mx


def grade(img, strength=1.0, seed=7):
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    H, W = a.shape[:2]
    hue, sat, val = rgb_to_hsv(a)
    lum = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]

    # 1. Selective saturation by hue: red stays, skin mostly stays, cool hues die.
    def band(c, w):
        d = np.minimum(np.abs(hue - c), 360 - np.abs(hue - c))
        return np.clip(1 - d / w, 0, 1)
    red = np.maximum(band(0, 22), band(360, 22))
    skin = band(25, 22)
    keep = np.clip(0.18 + 0.82 * red + 0.62 * skin, 0, 1)        # 0.18 = everything else
    keep = 1 - (1 - keep) * strength
    a = lum + (a - lum) * keep[..., None]

    # 2. Black point and mids down.
    bp = 0.035 * strength
    a = np.clip((a - bp) / (1 - bp), 0, 1)
    a = a ** (1 + 0.12 * strength)                                 # gamma darkens mids a touch

    # 3. S-curve contrast around a low pivot so highlights pop out of the dark.
    # Shadows below the pivot are pressed towards black; everything above is
    # stretched upwards so faces, rim light and red read harder.
    k = 1 + 0.7 * strength
    piv = 0.16
    lo = piv * (a / piv) ** k
    hi = piv + (1 - piv) * (1 - (1 - np.clip((a - piv) / (1 - piv), 0, 1)) ** (1 + 0.8 * strength))
    a = np.where(a < piv, lo, hi)

    # 4. Vignette into pure black.
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rx = (xx - W / 2) / (W / 2); ry = (yy - H / 2) / (H / 2)
    r = np.sqrt(rx ** 2 * 0.85 + ry ** 2 * 1.1)
    vig = np.clip(1 - np.clip(r - 0.55, 0, None) ** 1.5 * 0.85 * strength, 0, 1)
    a = a * vig[..., None]

    # 5. Grain (luma only), slightly stronger in the shadows.
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 0.012, (H, W, 1)).astype(np.float32)
    a = np.clip(a + n * (1.2 - a.mean(-1, keepdims=True)), 0, 1)
    return Image.fromarray((a * 255 + 0.5).astype(np.uint8))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("src"); p.add_argument("dst")
    p.add_argument("--strength", type=float, default=1.0)
    o = p.parse_args()
    grade(Image.open(o.src), o.strength).save(o.dst)
