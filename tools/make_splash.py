#!/usr/bin/env python3
"""Build the boot splash (D-068) from design/brand/logo2.png.

    python tools/make_splash.py        writes splash/starstack-splash.png + .rgb565 (480x320)

Same look as the touchscreen's "Starting printer" screen: the logo on a light rounded plate,
centered on the UI's black. The .rgb565 file is the raw framebuffer image (little-endian RGB565,
the TFT35's /dev/fb0 format) that splash/starstack-splash.sh copies straight to the screen.
Needs Pillow (on the PC that builds it; the Pi only uses the generated files).
"""
import os
import struct

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 480, 320
BG, PLATE = (10, 10, 10), (248, 248, 248)


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
    out = os.path.join(ROOT, "splash")
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, "starstack-splash.png"))
    raw = bytearray()
    for r, g, b in img.getdata():
        raw += struct.pack("<H", ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))
    with open(os.path.join(out, "starstack-splash.rgb565"), "wb") as f:
        f.write(raw)
    print(f"splash: {W}x{H}, logo {lw}x{lh}, raw {len(raw)} bytes")


if __name__ == "__main__":
    main()
