#!/usr/bin/python3
"""STARSTACK: boot progress bar under the logo on the touchscreen (D-070).

Installed to /usr/local/lib/starstack/ by install.sh; started by starstack-splash.sh at boot
(as root), after the logo is drawn. Fills a bar under the logo from the time since power-up and
how long the last boot took (/var/lib/starstack/boot_seconds, written by the touchscreen app when
Home first shows). If the screen app's X server paints over the logo while it starts, the logo is
put back, so there is no black gap. Stops as soon as the touchscreen app shows its first screen
(it creates /run/starstack/ui-up). The app's "Starting printer" screen then continues the same bar.
If the app still isn't up FAIL_AFTER into the boot, shows "The touchscreen app didn't start" with
the printer's address for Mainsail instead of a logo that looks frozen (D-079), and keeps it there
(the app's restarts redraw the logo) until the app does come up.
System python3 only (no Pillow): writes RGB565 pixels to /dev/fb0.
"""
import json
import math
import os
import socket
import struct
import time

SHARE = "/usr/local/share/starstack"
IMG = SHARE + "/starstack-splash-boot.rgb565"  # logo + empty bar track
FAIL_IMG = SHARE + "/starstack-splash-fail.rgb565"  # "The touchscreen app didn't start"
GLYPHS = SHARE + "/starstack-glyphs"  # .rgb565 + .json: characters for the address line
STATE = "/var/lib/starstack"
RUN = "/run/starstack"
UI_UP = RUN + "/ui-up"
STRIDE = 480 * 2
X0, Y0, BW, BH = 140, 236, 200, 6  # under the logo plate (plate ends at y=210)
# stop at the latest this long after the screen app's X server starts (D-072). Generous: the
# app can take ~12 s to load during boot and its cover takes over the bar when it's up
X_GRACE = 25
FAIL_AFTER = 120  # seconds of uptime (or 3x the usual boot if that's longer)
LOGO_ROWS = slice(110 * STRIDE, 211 * STRIDE)  # the plate: used to notice it was painted over


def rgb565(r, g, b):
    return struct.pack("<H", ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))


TRACK, FILL = rgb565(0x28, 0x28, 0x28), rgb565(0x00, 0xAC, 0xC7)  # theme @lines / @accent
BG = rgb565(10, 10, 10)  # splash background (tools/make_splash.py)


def uptime():
    with open("/proc/uptime") as f:
        return float(f.read().split()[0])


def expected():
    try:
        with open(os.path.join(STATE, "boot_seconds")) as f:
            return min(180.0, max(15.0, float(f.read())))
    except (OSError, ValueError):
        return 35.0


def progress(elapsed, total):
    # same curve as ks_includes/starstack.py progress(): 90 % at the expected time, then creeps
    if elapsed <= total:
        return 0.9 * elapsed / total
    return 0.9 + 0.09 * (1 - math.exp(-(elapsed - total) / 20))


def setup_run_dir():
    # /run/starstack belongs to the printer user (owner of /var/lib/starstack) so the
    # touchscreen app can write ui-up there; clear anything left from before
    os.makedirs(RUN, exist_ok=True)
    try:
        st = os.stat(STATE)
        os.chown(RUN, st.st_uid, st.st_gid)
    except OSError:
        pass
    for name in ("ui-up", "boot-recorded"):
        try:
            os.remove(os.path.join(RUN, name))
        except OSError:
            pass


def bar_rows(fill):
    rows = []
    for y in range(BH):
        inset = 1 if y in (0, BH - 1) else 0  # soften the corners
        line = bytearray(FILL * fill + TRACK * (BW - fill))
        if inset:
            line[0:2] = line[-2:] = BG
        rows.append(bytes(line))
    return rows


def x_running():
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                with open(f"/proc/{pid}/comm") as f:
                    if f.read().strip() == "Xorg":
                        return True
            except OSError:
                pass
    return False


def address():
    """This printer's IPv4 address on the network, or None (no packet is sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sk:
            sk.connect(("10.255.255.255", 1))
            ip = sk.getsockname()[0]
        return None if ip.startswith("127.") else ip
    except OSError:
        return None


def fail_frame(ip):
    """The 'didn't start' screen with 'http://<ip>' (or 'no network') written under it."""
    with open(FAIL_IMG, "rb") as f:
        frame = bytearray(f.read())
    with open(GLYPHS + ".json") as f:
        g = json.load(f)
    with open(GLYPHS + ".rgb565", "rb") as f:
        strip = f.read()
    chars = g["chars"]
    text = ["NONET"] if ip is None else [c for c in "http://" + ip if c in chars]
    width = sum(chars[c][1] for c in text)
    x = max(0, (480 - width) // 2)
    for c in text:
        cx, w = chars[c]
        for y in range(g["height"]):
            src = (y * g["width"] + cx) * 2
            dst = (g["y"] + y) * STRIDE + x * 2
            frame[dst : dst + w * 2] = strip[src : src + w * 2]
        x += w
    return bytes(frame)


def watch(fd, deadline):
    """Bar is done but the app isn't up: after the deadline, show the 'didn't start' screen."""
    frame, shown_ip = None, ""
    while not os.path.exists(UI_UP):
        if uptime() >= deadline:
            ip = address()
            if frame is None or ip != shown_ip:
                frame, shown_ip = fail_frame(ip), ip
            os.lseek(fd, 0, os.SEEK_SET)
            if os.read(fd, len(frame)) != frame and not os.path.exists(UI_UP):
                os.lseek(fd, 0, os.SEEK_SET)
                os.write(fd, frame)
        time.sleep(1)


def main():
    with open(IMG, "rb") as f:
        logo = f.read()
    setup_run_dir()
    total = expected()
    deadline = max(FAIL_AFTER, 3 * total)
    fd = os.open("/dev/fb0", os.O_RDWR)
    last, n, end = -1, 0, None
    while not os.path.exists(UI_UP) and uptime() < deadline:
        if end is not None and time.monotonic() > end:
            break  # X has been up a while: leave the screen to the app (D-072)
        # Checked once a second only: keep this loop light while everything else is loading
        if end is None and n % 4 == 0 and x_running():
            end = time.monotonic() + X_GRACE
        n += 1
        os.lseek(fd, LOGO_ROWS.start, os.SEEK_SET)
        if os.read(fd, LOGO_ROWS.stop - LOGO_ROWS.start) != logo[LOGO_ROWS]:  # X cleared it
            if os.path.exists(UI_UP):
                break
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, logo)
            last = -1
        fill = int(BW * progress(uptime(), total))
        if fill != last and not os.path.exists(UI_UP):
            for y, row in enumerate(bar_rows(fill)):
                os.lseek(fd, (Y0 + y) * STRIDE + X0 * 2, os.SEEK_SET)
                os.write(fd, row)
            last = fill
        time.sleep(0.25)
    watch(fd, deadline)
    os.close(fd)


if __name__ == "__main__":
    try:
        main()
    except OSError:
        pass  # never fail the boot over a progress bar
