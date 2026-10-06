#!/usr/bin/env python3
"""Build the boot splash (D-068, D-073) from design/brand/logo2.png.

    python tools/make_splash.py        writes splash/starstack-splash[-boot].png + .rgb565 (480x320)

Same look as the touchscreen's "Starting printer" screen: the logo on a light rounded plate,
centered on the UI's black. Two versions:
  starstack-splash       logo only (shutdown / power-off)
  starstack-splash-boot  logo + empty progress-bar track (boot and while the UI restarts); the
                         bar is filled by splash/starstack-bootbar.py, then by the touchscreen
                         app's "Starting printer" cover, which draws this same PNG (pixel-identical)
The .rgb565 files are raw framebuffer images (little-endian RGB565, the TFT35's /dev/fb0 format)
that splash/starstack-splash.sh copies straight to the screen.
Needs Pillow (on the PC that builds it; the Pi only uses the generated files).
"""
import os
import struct

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 480, 320
BG, PLATE = (10, 10, 10), (248, 248, 248)
TRACK = (0x28, 0x28, 0x28)
BAR = (140, 236, 200, 6)  # x, y, w, h: keep in sync with starstack-bootbar.py and ss_starting.py


def track(img):
    # 6 px bar with the corner pixels cut, same shape the bar is filled with
    x, y, w, h = BAR
    d = ImageDraw.Draw(img)
    d.rectangle((x, y + 1, x + w - 1, y + h - 2), fill=TRACK)
    d.rectangle((x + 1, y, x + w - 2, y + h - 1), fill=TRACK)


def save(img, name):
    out = os.path.join(ROOT, "splash")
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, name + ".png"))
    raw = bytearray()
    for r, g, b in img.getdata():
        raw += struct.pack("<H", ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))
    with open(os.path.join(out, name + ".rgb565"), "wb") as f:
        f.write(raw)
    return len(raw)


def main():
    logo = Image.open(os.path.join(ROOT, "design", "brand", "logo2.png")).convert("RGBA")
    lw = 300
    lh = round(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    pw, ph = lw + 2 * 22, lh + 2 * 16
    img = Image.new("RGB", (W, H), BG)
    x0, y0 = (W - pw) // 2, (H - ph) // 2
    ImageDraw.Draw(img).rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=12, fill=PLATE)
    img.paste(logo, (x0 + 22, y0 + 16), logo)
    n = save(img, "starstack-splash")
    track(img)
    save(img, "starstack-splash-boot")
    print(f"splash: {W}x{H}, logo {lw}x{lh}, raw {n} bytes, + boot version with bar track")


if __name__ == "__main__":
    main()
