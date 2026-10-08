#!/usr/bin/python3
"""STARSTACK: update helper (klipper-ui D-087). Runs as the printer user (starstack-update.service).

"Update everything" on the touchscreen or in Mainsail runs Moonraker's updater. This helper finishes
the job so one tap is enough:

1. Tested versions: klipper-ui ships the Klipper/Moonraker versions we tested (update/versions.conf,
   included in moonraker.conf). Moonraker updates klipper-ui after Klipper, so when that file changes
   the helper restarts Moonraker (it reads the file at start) and installs the newly pinned versions.
2. Board firmware: when the board's firmware isn't the host's Klipper version and the printer is
   idle, it builds the firmware with the printer's saved build config and flashes it through the
   board's Katapult bootloader (D-083). Only on printers set up for it (install.sh --printer s1).

Never while printing or paused, never while Moonraker is updating. Messages go to the printer's
console (both UIs) and ~/printer_data/logs/starstack-update.log; the touchscreen's Updates page
reads /run/starstack/board-firmware.
  starstack-update.py            run (the service)
  starstack-update.py --check    show what it would do now, change nothing
  starstack-update.py --flash    flash the board now (if idle), even when the versions match
"""

import configparser
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HOME = os.path.expanduser("~")
REPO = os.environ.get("STARSTACK_REPO", os.path.join(HOME, "klipper-ui"))
MOON = "http://localhost:7125"
KLIPPER = os.path.join(HOME, "klipper")
KLIPPY_PY = os.path.join(HOME, "klippy-env", "bin", "python")
FLASHTOOL = os.path.join(HOME, "katapult", "scripts", "flashtool.py")
STATE_DIR = "/var/lib/starstack"
STATE = os.path.join(STATE_DIR, "update-state.json")
# e.g. "s1": which config/<printer>/firmware.conf to use (written by install.sh --printer=)
PRINTER = os.path.join(STATE_DIR, "printer")
BUILD = os.path.join(STATE_DIR, "firmware-build")
STATUS = "/run/starstack/board-firmware"
LOG = os.path.join(HOME, "printer_data", "logs", "starstack-update.log")
PINS = os.path.join(REPO, "update", "versions.conf")
POLL = 15
SETTLE = 45  # seconds after an update or Klipper restart before touching the board
MAX_TRIES = 2  # flash attempts per Klipper version


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line, flush=True)
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > 1_000_000:
            os.replace(LOG, LOG + ".1")
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def api(path, method="GET", timeout=10):
    req = urllib.request.Request(MOON + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r).get("result")
    except (urllib.error.URLError, OSError, ValueError):
        return None


def query(objects):
    r = api(
        "/printer/objects/query?"
        + "&".join(urllib.parse.quote(o, safe="=,") for o in objects)
    )
    return (r or {}).get("status", {})


def say(msg, error=False):
    """Message on the printer's console (Mainsail + touchscreen), when Klipper is running."""
    log(msg)
    kind = "error" if error else "echo"
    script = f'RESPOND TYPE={kind} MSG="{msg}"'
    api("/printer/gcode/script?script=" + urllib.parse.quote(script), "POST", timeout=5)


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(s):
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f)
    os.replace(tmp, STATE)


def set_status(state, message="", host="", mcu=""):
    try:
        os.makedirs(os.path.dirname(STATUS), exist_ok=True)
        with open(STATUS + ".tmp", "w") as f:
            json.dump(
                {
                    "state": state,
                    "message": message,
                    "host": host,
                    "mcu": mcu,
                    "time": time.time(),
                },
                f,
            )
        os.replace(STATUS + ".tmp", STATUS)
    except OSError:
        pass


def pins_hash():
    try:
        with open(PINS, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return ""


def update_status():
    return api("/machine/update/status") or {}


def busy_printing():
    s = query(["print_stats=state"])
    return s.get("print_stats", {}).get("state") in ("printing", "paused")


def firmware_profile():
    """(build config path) for this printer's board, or None when not set up for board updates."""
    try:
        with open(PRINTER) as f:
            name = f.read().strip()
    except OSError:
        return None
    cfg = configparser.ConfigParser(inline_comment_prefixes=("#",))
    folder = os.path.join(REPO, "config", name)
    if not cfg.read(os.path.join(folder, "firmware.conf")) or not cfg.has_section(
        "firmware"
    ):
        return None
    if cfg.get("firmware", "method", fallback="") != "katapult":
        return None
    path = os.path.join(folder, cfg.get("firmware", "build_config"))
    return path if os.path.exists(path) else None


def versions():
    """(klippy state, state message, host version, board version or None)."""
    info = api("/printer/info") or {}
    state, msg, host = (
        info.get("state", "?"),
        info.get("state_message", ""),
        info.get("software_version", ""),
    )
    mcu = None
    if state == "ready":
        mcu = query(["mcu=mcu_version"]).get("mcu", {}).get("mcu_version")
    return state, msg, host, mcu


def mismatch(state, msg, host, mcu):
    if not host:
        return False
    if state == "ready":
        return bool(mcu) and mcu != host
    # Klipper refuses to run with firmware that doesn't speak its protocol
    low = msg.lower()
    return state in ("error", "shutdown") and ("protocol" in low or "firmware" in low)


# ---------------------------------------------------------------- 1. tested versions


def apply_pins(st):
    """klipper-ui brought new pins: restart Moonraker so it reads them, then install them."""
    say("StarStack update: installing the tested Klipper/Moonraker versions")
    api("/machine/services/restart?service=moonraker", "POST")
    for _ in range(60):  # Moonraker back
        time.sleep(2)
        if api("/server/info"):
            break
    time.sleep(5)
    api("/machine/update/refresh", "POST", timeout=180)
    for app in ("moonraker", "klipper"):
        info = update_status().get("version_info", {}).get(app, {})
        cur, new = info.get("version"), info.get("remote_version")
        if new and new not in ("?", cur) and info.get("is_valid", True):
            log(f"updating {app}: {cur} -> {new}")
            api(f"/machine/update/{app}", "POST", timeout=900)
            # wait for that update (and Moonraker's restart) to finish
            for _ in range(150):
                time.sleep(4)
                u = api("/machine/update/status")
                if u and not u.get("busy"):
                    break
    st["pins"] = pins_hash()
    st["settle_until"] = time.time() + SETTLE
    save_state(st)
    log("tested versions applied")


# ---------------------------------------------------------------- 2. board firmware


def board_device():
    """The board's USB serial device: the one in printer.cfg, or Katapult if it's already there."""
    kat = sorted(glob.glob("/dev/serial/by-id/usb-katapult_*"))
    if kat:
        return kat[0]
    s = query(["configfile=settings"]).get("configfile", {}).get("settings", {})
    dev = s.get("mcu", {}).get("serial")
    if dev and os.path.exists(dev):
        return dev
    found = sorted(glob.glob("/dev/serial/by-id/usb-Klipper_*"))
    return found[0] if len(found) == 1 else None


def run(cmd, timeout):
    r = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, check=False
    )
    out = (r.stdout + r.stderr).strip().splitlines()
    for line in out[-15:]:
        log("   " + line)
    return r.returncode == 0


def wait_klipper(target, seconds=90):
    for _ in range(seconds // 3):
        time.sleep(3)
        info = api("/printer/info") or {}
        if info.get("state") == target:
            return True
    return False


def flash(build_cfg, host):
    set_status("updating", "Building the board firmware", host)
    say(
        "Board firmware: updating it to match Klipper (about 2 minutes). Don't switch the printer off."
    )
    os.makedirs(BUILD, exist_ok=True)
    cfg = os.path.join(BUILD, "config")
    out = os.path.join(BUILD, "out") + "/"
    shutil.copy(build_cfg, cfg)
    make = ["make", "-C", KLIPPER, f"KCONFIG_CONFIG={cfg}", f"OUT={out}"]
    if not (
        run(make + ["olddefconfig"], 120)
        and run(make + ["clean"], 120)
        and run(make + ["-j4"], 900)
    ):
        return "the firmware didn't build"
    binary = os.path.join(out, "klipper.bin")
    dev = board_device()
    if not dev:
        return "the board's USB device wasn't found"
    set_status("updating", "Flashing the board", host)
    api("/machine/services/stop?service=klipper", "POST")
    time.sleep(3)
    ok = run([KLIPPY_PY, FLASHTOOL, "-d", dev, "-f", binary], 300)
    api("/machine/services/start?service=klipper", "POST")
    if not ok:
        return "flashing didn't finish (the board's Katapult bootloader is still there: it can be retried)"
    if not wait_klipper("ready", 120):
        return "Klipper didn't come back as ready after flashing"
    return None


def board_check(st, check_only=False, force=False):
    build_cfg = firmware_profile()
    if not build_cfg:
        set_status("n/a", "This printer isn't set up for board updates")
        return "not set up for board updates"
    state, msg, host, mcu = versions()
    if not force and not mismatch(state, msg, host, mcu):
        if state == "ready":
            set_status("ok", "", host, mcu or "")
        return (
            f"board firmware matches ({mcu})"
            if state == "ready"
            else f"Klipper is {state}"
        )
    if busy_printing():
        return "printing: board update waits"
    if update_status().get("busy"):
        return "Moonraker is updating: board update waits"
    if time.time() < st.get("settle_until", 0):
        return "waiting for things to settle after an update"
    tries = st.get("fw", {})
    if not force and tries.get("host") == host and tries.get("count", 0) >= MAX_TRIES:
        set_status(
            "failed",
            "Board firmware update failed: see starstack-update.log",
            host,
            mcu or "",
        )
        return f"gave up after {MAX_TRIES} tries for {host}"
    if check_only:
        return f"would flash the board: {mcu or state} -> {host}"
    st["fw"] = {
        "host": host,
        "count": (tries.get("count", 0) if tries.get("host") == host else 0) + 1,
    }
    save_state(st)
    log(f"board firmware {mcu or '(' + state + ')'} -> {host}")
    err = flash(build_cfg, host)
    state, msg, host2, mcu2 = versions()
    if err is None and not mismatch(state, msg, host2, mcu2):
        st["fw"] = {"host": host2, "count": 0}
        save_state(st)
        set_status("ok", "", host2, mcu2 or "")
        say(f"Board firmware updated to {mcu2}.")
        return "flashed"
    err = err or f"the board still reports {mcu2}"
    set_status("failed", "Board firmware update failed: " + err, host2, mcu2 or "")
    say(
        "Board firmware update failed: " + err + ". Details: starstack-update.log",
        error=True,
    )
    return "failed: " + err


# ---------------------------------------------------------------- main


def step(st, check_only=False):
    if api("/server/info") is None:
        return "Moonraker not reachable"
    if update_status().get("busy"):
        st["settle_until"] = time.time() + SETTLE
        return "Moonraker is updating"
    if st.get("pins") is None:  # first run: the current pins are what's installed
        st["pins"] = pins_hash()
        save_state(st)
    elif st["pins"] != pins_hash():
        if busy_printing():
            return "new tested versions wait until the print is done"
        if check_only:
            return "would install the new tested Klipper/Moonraker versions"
        apply_pins(st)
        return "tested versions applied"
    return board_check(st, check_only)


def main():
    st = load_state()
    if "--check" in sys.argv:
        print(step(st, check_only=True))
        return
    if "--flash" in sys.argv:
        print(board_check(st, force=True))
        return
    log("update helper started")
    last = None
    while True:
        try:
            result = step(st)
        except Exception as e:  # keep running: a bad poll must not stop the helper
            result = f"error: {e!r}"
        if result != last:
            log(result)
            last = result
        time.sleep(POLL)


if __name__ == "__main__":
    main()
