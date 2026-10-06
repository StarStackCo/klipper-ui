#!/usr/bin/env python3
"""Build the boot splash (D-068, D-073) from design/brand/logo2.png.

    python tools/make_splash.py        writes splash/starstack-splash[-boot].png + .rgb565 (480x320)

Same look as the touchscreen's "Starting printer" screen: the logo on a light rounded plate,
centered on the UI's black. Two versions:
  starstack-splash       logo only (shutdown / power-off)
  starstack-splash-boot  logo + empty progress-bar track (boot and while the UI restarts); the
                         bar is filled by splash/starstack-bootbar.py, then by the touchscreen
                         app's "Starting printer" cover, which draws this same PNG (pixel-identical)
  starstack-splash-fail   logo + "The touchscreen app didn't start" (D-079): shown by the bar
                         program if the app never comes up; it writes the printer's address
                         under it using starstack-glyphs.rgb565 (+ .json: where each character is)
The .rgb565 files are raw framebuffer images (little-endian RGB565, the TFT35's /dev/fb0 format)
that splash/starstack-splash.sh copies straight to the screen.
Needs Pillow (on the PC that builds it; the Pi only uses the generated files).
"""
import json
import os
import struct

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 480, 320
BG, PLATE = (10, 10, 10), (248, 248, 248)
TRACK = (0x28, 0x28, 0x28)
FONTS = os.path.join(os.path.dirname(ROOT), "KlipperScreen-starstack", "styles", "starstack", "fonts")
TEXT, MUTED, ACCENT = (0xFA, 0xFA, 0xFA), (0xA1, 0xA1, 0xA1), (0x00, 0xAC, 0xC7)
GLYPHS = "0123456789.:/htp"  # enough for "http://192.168.0.102"
ADDR_Y, ADDR_H = 278, 24  # address line (bar program draws it), keep in sync with bootbar
BAR = (140, 236, 200, 6)  # x, y, w, h: keep in sync with starstack-bootbar.py and ss_starting.py


def track(img):
    # 6 px bar with the corner pixels cut, same shape the bar is filled with
    x, y, w, h = BAR
    d = ImageDraw.Draw(img)
    d.rectangle((x, y + 1, x + w - 1, y + h - 2), fill=TRACK)
    d.rectangle((x + 1, y, x + w - 2, y + h - 1), fill=TRACK)


def font(weight, size):
    return ImageFont.truetype(os.path.join(FONTS, f"PublicSans-{weight}.ttf"), size)


def centered(img, y, text, fnt, fill):
    d = ImageDraw.Draw(img)
    w = d.textlength(text, font=fnt)
    d.text(((W - w) / 2, y), text, font=fnt, fill=fill)


def glyph_strip():
    """One row of characters for the address line; returns (image, {char: [x, width]})."""
    fnt = font("SemiBold", 17)
    pieces = {c: round(fnt.getlength(c)) for c in GLYPHS}
    nonet = "No network: check the cable or Wi-Fi"
    pieces["NONET"] = round(font("Regular", 14).getlength(nonet))
    img = Image.new("RGB", (sum(pieces.values()), ADDR_H), BG)
    d, x, table = ImageDraw.Draw(img), 0, {}
    for c, w in pieces.items():
        if c == "NONET":
            d.text((x, 4), nonet, font=font("Regular", 14), fill=MUTED)
        else:
            d.text((x, 1), c, font=fnt, fill=ACCENT)
        table[c] = [x, w]
        x += w
    return img, table


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
    fail = Image.new("RGB", (W, H), BG)
    fail.paste(img.crop((0, 0, W, 215)), (0, -24))  # logo plate moved up a little for 3 lines
    centered(fail, 206, "The touchscreen app didn't start", font("ExtraBold", 17), TEXT)
    centered(fail, 236, "Restart the printer, or open Mainsail in a browser:", font("Regular", 14), MUTED)
    save(fail, "starstack-splash-fail")
    strip, table = glyph_strip()
    save(strip, "starstack-glyphs")
    with open(os.path.join(ROOT, "splash", "starstack-glyphs.json"), "w") as f:
        json.dump({"height": ADDR_H, "y": ADDR_Y, "width": strip.width, "chars": table}, f)
    print(f"splash: {W}x{H}, logo {lw}x{lh}, raw {n} bytes, + boot version with bar track")


if __name__ == "__main__":
    main()
