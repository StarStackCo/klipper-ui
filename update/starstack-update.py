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

3. Health check and undo (D-092): after any update, Moonraker, Klipper, the touchscreen app and the
   board must be healthy within 5 minutes, or every changed part goes back to the last known good
   versions. The touchscreen's "Undo last update" goes back one update (/run/starstack/undo-request).

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
GIT_REPOS = {
    "klipper": KLIPPER,
    "moonraker": os.path.join(HOME, "moonraker"),
    "klipper-ui": REPO,
    "KlipperScreen": os.path.join(HOME, "KlipperScreen"),
    "mainsail-config": os.path.join(HOME, "mainsail-config"),
}
MAINSAIL_INFO = os.path.join(HOME, "mainsail", "release_info.json")
KS_UNIT = "/etc/systemd/system/KlipperScreen.service"
CONFIG_DIR = os.path.join(HOME, "printer_data", "config")
CONFIG_FILES = ("printer.cfg", "moonraker.conf", "KlipperScreen.conf")
GOOD_DIR = os.path.join(
    STATE_DIR, "good"
)  # config copy of the last known good (+ ".prev")
HEALTH = "/run/starstack/update-health"  # read by the touchscreen's Updates page
UNDO_REQUEST = "/run/starstack/undo-request"  # written by its "Undo last update" button
HEALTH_WAIT = 300  # seconds for everything to be healthy after an update (user: 5 min)
HEALTH_STEADY = (
    60  # ...and it must stay healthy this long before the update counts as good
)
CONFIG_REFRESH = 3600  # keep the good config copy up to date with the user's own edits
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


# ---------------------------------------------------------------- 3. health check and undo (D-092)
# "Last known good": the exact versions (git commits, Mainsail release) of a printer that was idle
# and healthy, plus a copy of its main config files. After any update (touchscreen, Mainsail or by
# hand) the helper waits up to HEALTH_WAIT for Moonraker, Klipper (ready), the touchscreen app and
# the board firmware; if they aren't all healthy by then, it puts every changed part back to the
# last good versions. "Undo last update" (touchscreen) goes back to the record before that.


def git(path, *args, timeout=60):
    r = subprocess.run(
        ["git", "-C", path, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return r.stdout.strip() if r.returncode == 0 else None


def current_versions():
    v = {}
    for name, path in GIT_REPOS.items():
        if os.path.isdir(os.path.join(path, ".git")):
            v[name] = git(path, "rev-parse", "HEAD")
    try:
        with open(MAINSAIL_INFO) as f:
            v["mainsail"] = json.load(f).get("version")
    except (OSError, ValueError):
        pass
    return v


def file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def service_active(unit):
    r = subprocess.run(
        ["systemctl", "is-active", unit], capture_output=True, text=True, check=False
    )
    return r.stdout.strip() == "active"


def restart(unit):
    """Restart a service without Moonraker (the helper's unit has Moonraker's polkit group)."""
    r = subprocess.run(
        ["systemctl", "--no-ask-password", "restart", unit],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    log(f"restart {unit}: {'ok' if r.returncode == 0 else r.stderr.strip()}")


def healthy():
    """(True, "") or (False, why) for the printer's software after an update."""
    if api("/server/info") is None:
        return False, "Moonraker isn't answering"
    state, msg, host, mcu = versions()
    if state != "ready":
        first = (msg.strip().splitlines() or [""])[0][:100]
        return False, f"Klipper is {state}" + (f" ({first})" if first else "")
    if os.path.exists(KS_UNIT) and not service_active("KlipperScreen"):
        return False, "the touchscreen app isn't running"
    if firmware_profile() and mismatch(state, msg, host, mcu):
        return False, "the board firmware doesn't match Klipper yet"
    return True, ""


def set_health(st, state, message):
    prev = st.get("prev")
    info = {
        "state": state,
        "message": message,
        "time": time.time(),
        "can_undo": bool(prev),
        "undo_to": time.strftime("%Y-%m-%d %H:%M", time.localtime(prev["time"]))
        if prev
        else "",
    }
    try:
        os.makedirs(os.path.dirname(HEALTH), exist_ok=True)
        with open(HEALTH + ".tmp", "w") as f:
            json.dump(info, f)
        os.replace(HEALTH + ".tmp", HEALTH)
    except OSError:
        pass


def record_good(st, cur):
    """These versions work: keep them (and the config) as the new last known good."""
    if st.get("good") and st["good"]["versions"] != cur:
        if os.path.isdir(GOOD_DIR + ".prev"):
            shutil.rmtree(GOOD_DIR + ".prev")
        if os.path.isdir(GOOD_DIR):
            os.replace(GOOD_DIR, GOOD_DIR + ".prev")
        st["prev"] = dict(st["good"], config_dir=GOOD_DIR + ".prev")
    save_config(st, cur)


def save_config(st, cur):
    os.makedirs(GOOD_DIR, exist_ok=True)
    hashes = {}
    for name in CONFIG_FILES:
        src = os.path.join(CONFIG_DIR, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(GOOD_DIR, name))
            hashes[name] = file_hash(src)
    branches = {
        n: git(p, "branch", "--show-current")
        for n, p in GIT_REPOS.items()
        if n in cur and n != "mainsail"
    }
    st["good"] = {
        "time": time.time(),
        "versions": cur,
        "branches": branches,
        "config": hashes,
        "config_dir": GOOD_DIR,
    }
    st["config_saved"] = time.time()
    save_state(st)


def summary(old, new):
    names = [n for n in sorted(set(old) | set(new)) if old.get(n) != new.get(n)]
    return ", ".join(names) or "nothing"


def undo(st, target, reason, auto):
    cur = current_versions()
    changed = [n for n, v in target["versions"].items() if cur.get(n) != v]
    what = ", ".join(changed) or "nothing"
    head = "Update undone automatically" if auto else "Undoing the last update"
    say(f"StarStack: {head} ({what}): {reason}", error=auto)
    set_health(st, "undoing", f"Putting back the previous versions: {what}")
    for name in changed:
        if name == "mainsail":
            continue
        path, sha = GIT_REPOS[name], target["versions"][name]
        branch = target.get("branches", {}).get(name)
        if branch and git(path, "branch", "--show-current") != branch:
            git(path, "checkout", "-q", branch)
        ok = git(path, "reset", "-q", "--hard", sha) is not None
        log(f"{name}: back to {sha[:9]}" + ("" if ok else " FAILED"))
    restored = False
    if auto:  # config files changed during this update (not the user's earlier edits)
        since = st.get("changed_at", time.time()) - 60
        for name, h in target.get("config", {}).items():
            dst = os.path.join(CONFIG_DIR, name)
            src = os.path.join(target["config_dir"], name)
            try:
                newer = os.path.getmtime(dst) >= since
            except OSError:
                newer = True
            if file_hash(dst) != h and newer and os.path.isfile(src):
                if os.path.isfile(dst):
                    shutil.copy2(dst, dst + ".pre-undo")
                shutil.copy2(src, dst)
                restored = True
                log(f"config {name} restored (the changed one is {name}.pre-undo)")
    if (
        restored
        or {"moonraker", "klipper-ui"} & set(changed)
        or api("/server/info") is None
    ):
        restart("moonraker")
        for _ in range(60):
            time.sleep(2)
            if api("/server/info"):
                break
    if restored or {"klipper", "klipper-ui", "mainsail-config"} & set(changed):
        restart("klipper")
    if "KlipperScreen" in changed:
        restart("KlipperScreen")
    if "mainsail" in changed:
        api("/machine/update/rollback?name=mainsail", "POST", timeout=120)
    api(
        "/machine/update/refresh", "POST", timeout=180
    )  # Mainsail/touchscreen show the right versions
    st["pins"] = pins_hash()  # the pins now match the versions put back
    st["fw"] = {}
    st["settle_until"] = time.time() + SETTLE
    st.pop("changed_at", None)
    st.pop("healthy_since", None)
    if not auto:  # the previous record becomes the good one; one step of undo only
        st["good"], st["prev"] = dict(target, config_dir=GOOD_DIR), None
        if os.path.isdir(GOOD_DIR):
            shutil.rmtree(GOOD_DIR)
        if os.path.isdir(GOOD_DIR + ".prev"):
            os.replace(GOOD_DIR + ".prev", GOOD_DIR)
    st["undone"] = {"time": time.time(), "reason": reason, "auto": auto, "what": what}
    save_state(st)
    msg = (
        f"Update undone ({what}): {reason}" if auto else f"Last update undone ({what})"
    )
    set_health(st, "undone", msg)
    if wait_klipper("ready", 90):  # the first message went out while Klipper was down
        say(
            "StarStack: " + msg + ". Everything is back on the previous versions.",
            error=auto,
        )
    return msg


def health_step(st, check_only=False):
    """None when there's nothing to do, else a status line for the log."""
    cur = current_versions()
    good = st.get("good")
    if check_only:
        if not good:
            return "health: no known-good record yet"
        if cur == good["versions"]:
            return "health: running the last known good versions"
        return f"health: new versions ({summary(good['versions'], cur)}): {healthy()[1] or 'healthy'}"
    if st.get("pins") and st["pins"] != pins_hash():
        st["changed_at"] = (
            time.time()
        )  # new tested versions are being installed: wait for them
        save_state(st)
        return None
    if os.path.exists(UNDO_REQUEST):
        try:
            os.remove(UNDO_REQUEST)
        except OSError:
            pass
        if busy_printing():
            set_health(st, "ok", "Undo waits: the printer is printing")
            return "undo requested while printing: ignored"
        if (api("/machine/update/status") or {}).get("busy"):
            set_health(st, "ok", "Undo waits: an update is running")
            return "undo requested while updating: ignored"
        if not st.get("prev"):
            set_health(st, "ok", "There is no earlier version to go back to")
            return "undo requested: nothing to go back to"
        return undo(st, st["prev"], "Undo button", auto=False)
    upd = api("/machine/update/status")
    if upd and upd.get("busy"):
        if good and cur != good["versions"]:
            st["changed_at"] = time.time()  # the 5 minutes start when updating finishes
            save_state(st)
        return None
    if not good or cur == good["versions"]:
        st.pop("changed_at", None)
        st.pop("healthy_since", None)
        if busy_printing():
            return None
        ok, _why = healthy()
        if ok and not good:
            log("recorded the last known good versions")
            save_config(st, cur)
            set_health(st, "ok", "")
        elif ok and time.time() - st.get("config_saved", 0) > CONFIG_REFRESH:
            save_config(
                st, cur
            )  # keep the config copy current with the user's own edits
        return None
    if "changed_at" not in st:
        st["changed_at"] = time.time()
        save_state(st)
        log(f"new versions ({summary(good['versions'], cur)}): checking they work")
    ok, why = healthy()
    if not ok:
        st.pop("healthy_since", None)
    elif "healthy_since" not in st:
        st["healthy_since"] = time.time()
        save_state(st)
    # healthy for a whole minute: right after the change the services may not have restarted yet
    if ok and time.time() - st["healthy_since"] >= HEALTH_STEADY:
        record_good(st, cur)
        st.pop("changed_at", None)
        st.pop("healthy_since", None)
        save_state(st)
        set_health(st, "ok", "Last update checked: everything started")
        return "update checked: everything started"
    if ok:
        set_health(
            st,
            "checking",
            "Checking the update: everything started, making sure it stays up",
        )
        return "checking the update: healthy, waiting a minute"
    waited = time.time() - st["changed_at"]
    if waited < HEALTH_WAIT:
        set_health(
            st,
            "checking",
            f"Checking the update ({int((HEALTH_WAIT - waited) / 60) + 1} min left): {why}",
        )
        return f"checking the update: {why}"
    if (
        busy_printing()
    ):  # e.g. only the touchscreen app is down: never restart Klipper mid-print
        set_health(
            st,
            "checking",
            f"Update problem ({why}): undo waits until the print is done",
        )
        return f"update problem, waiting for the print: {why}"
    return undo(st, good, why, auto=True)


# ---------------------------------------------------------------- main


def step(st, check_only=False):
    health = health_step(st, check_only)
    rest = maintain(st, check_only)
    return " | ".join(x for x in (health, rest) if x)


def maintain(st, check_only=False):
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
    if not os.path.exists(HEALTH):
        set_health(st, "ok", "")
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
