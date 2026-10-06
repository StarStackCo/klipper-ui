#!/usr/bin/python3
"""STARSTACK: boot progress bar under the logo on the touchscreen (D-070).

Installed to /usr/local/lib/starstack/ by install.sh; started by starstack-splash.sh at boot
(as root), after the logo is drawn. Fills a bar under the logo from the time since power-up and
how long the last boot took (/var/lib/starstack/boot_seconds, written by the touchscreen app when
Home first shows). If the screen app's X server paints over the logo while it starts, the logo is
put back, so there is no black gap. Stops as soon as the touchscreen app shows its first screen
(it creates /run/starstack/ui-up), or after 3 minutes. The app's "Starting printer" screen then
continues the same bar. System python3 only (no Pillow): writes RGB565 pixels to /dev/fb0.
"""
import math
import os
import struct
import time

IMG = "/usr/local/share/starstack/starstack-splash-boot.rgb565"  # logo + empty bar track
STATE = "/var/lib/starstack"
RUN = "/run/starstack"
UI_UP = RUN + "/ui-up"
STRIDE = 480 * 2
X0, Y0, BW, BH = 140, 236, 200, 6  # under the logo plate (plate ends at y=210)
# stop at the latest this long after the screen app's X server starts (D-072). Generous: the
# app can take ~12 s to load during boot and its cover takes over the bar when it's up
X_GRACE = 25
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


def main():
    with open(IMG, "rb") as f:
        logo = f.read()
    setup_run_dir()
    total, end = expected(), time.monotonic() + 180
    fd = os.open("/dev/fb0", os.O_RDWR)
    last, n, x_seen = -1, 0, False
    while time.monotonic() < end and not os.path.exists(UI_UP):
        # Safety net: an older touchscreen app never says it's up, so never keep drawing over it.
        # Checked once a second only: keep this loop light while everything else is loading.
        if not x_seen and n % 4 == 0 and x_running():
            x_seen, end = True, min(end, time.monotonic() + X_GRACE)
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
    os.close(fd)


if __name__ == "__main__":
    try:
        main()
    except OSError:
        pass  # never fail the boot over a progress bar
