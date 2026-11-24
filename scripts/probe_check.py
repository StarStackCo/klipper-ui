#!/usr/bin/env python3
"""Z homing check for the S1 (D-NEW probe check, B-24).
Runs ON THE PI: scripts/pi.sh 'python3 -' < scripts/probe_check.py
Self-test of the pass/fail logic (any PC): python scripts/probe_check.py --selftest
Touchscreen (KlipperScreen fork, ss_probe_check): --json, no prompt, last line is
{"ok": bool, "reason": str, "fix": [str]} and the screen shows its own page.

Nozzle at a steady clean_temp (_PROBE_HOT), then at the homing point X133 Y185 it homes Z from
higher and higher starts (resonance and long descents caused misses and mid-air triggers, D-134,
D-140). Each home must travel as far down as the motor steps say the head went up, so its zero lands
within LIMIT_MM of the last one: a mid-air trigger stops short. (Run NEW probe check: every home and
probe fired in the air, the probe agreed with the home, and the head climbed into the top.) After
each home a PROBE at 5 mm/s must also read Z 0 within LIMIT_MM. Stops at the first failure and shows
the user a prompt on the touchscreen and Mainsail. Uses the configured homing_speed; never runs
while printing. The first home is the baseline: only a person can see that it touched the bed."""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request

API = "http://localhost:7125"
HEIGHTS = [5, 10, 20, 40]  # mm above the last home; the homing override adds 3. Real Z travel unmeasured
LIMIT_MM = 0.1  # D-140: at 5 mm/s good homes read 0.017 to 0.032, bad ones 0.3 to 1.1 or a miss
LIFT = "F300"  # D-109: Z moves up at 5 mm/s, faster hits the frame resonance

FAIL_TEXT = [
    "1. Turn the printer off and unplug it.",
    "2. Check the hotend: heatsink and nozzle screws tight, no plastic on the nozzle.",
    "3. Check the toolhead cable has slack with the head at the front left and Z down.",
    "4. Check nothing is stuck to the bed at the back right, under the homing point.",
    "5. Plug in, switch on and run the self-check again (Settings, Setup and tour).",
]


def judge(results):
    """results: list of (height, probe z, zero shift, error or None). Returns (ok, reason).
    shift: how far this home's zero sits above the last one, from motor steps (+ = fired early)."""
    for h, z, shift, err in results:
        if err:
            return False, "From Z %d: %s" % (h, err)
        if abs(shift) > LIMIT_MM:
            kind = "in mid-air, %.2f mm early" % shift if shift > 0 else "%.2f mm late" % -shift
            return False, "From Z %d the nozzle homed %s" % (h, kind)
        if abs(z) > LIMIT_MM:
            kind = "triggered %.2f mm above the bed" % -z if z < 0 else "triggered %.2f mm late" % z
            return False, "From Z %d the probe %s" % (h, kind)
    return True, "Homed from %s mm, probe read %s" % (
        ", ".join(str(r[0]) for r in results), ", ".join("%.3f" % r[1] for r in results))


def shift_mm(before, after, spm, sign):
    """(Z, steps) before and after a home: real move from the steps minus the move Klipper reports."""
    return round(sign * (after[1] - before[1]) / spm - (after[0] - before[0]), 3)


def selftest():
    assert judge([(5, 0.02, 0.01, None), (10, -0.03, -0.02, None)])[0]
    assert not judge([(5, 0.02, 0.0, None), (10, -0.4, 0.0, None)])[0]  # probe fired early
    assert "above the bed" in judge([(10, -0.4, 0.0, None)])[1]
    assert "late" in judge([(10, 1.1, 0.0, None)])[1]
    assert not judge([(40, 0.0, None, "No trigger on stepper_z after full movement")])[0]
    # Run NEW probe check: home and probe both fired in the air, so the probe alone read 0.018
    assert "mid-air" in judge([(20, 0.018, 21.5, None)])[1]
    # override lifts 3 then homes, ends at Z 3: from Z 5 that is 2 mm down
    assert shift_mm((5.0, 10000), (3.0, 10000 + 3200), 1600, -1) == 0.0  # 2 mm of steps: on the bed
    assert shift_mm((5.0, 10000), (3.0, 10000 - 1600), 1600, -1) == 3.0  # went up 1 mm: fired early
    print("selftest ok")


def get(path):
    with urllib.request.urlopen(API + path, timeout=30) as r:
        return json.load(r)["result"]


def gcode(script):
    """Runs G-code and waits for it to finish. Returns None or Klipper's error message."""
    print(">>> " + script.replace("\n", " | "), flush=True)
    req = urllib.request.Request(
        API + "/printer/gcode/script?script=" + urllib.parse.quote(script), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            r.read()
        return None
    except urllib.error.HTTPError as e:
        msg = json.load(e).get("error", {}).get("message", "HTTP %s" % e.code)
        print("!!! " + msg, flush=True)
        return msg


def pos():
    """(toolhead Z, stepper_z step count) from GET_POSITION's reply in Moonraker's G-code store."""
    t = time.time() - 0.5
    # M400 first: Moonraker returns once a move is queued, and the step count lags until it runs
    if gcode("M400\nGET_POSITION"):
        raise RuntimeError("GET_POSITION failed")
    text = "\n".join(m["message"] for m in get("/server/gcode_store?count=30")["gcode_store"]
                     if m["time"] >= t)
    return (float(re.findall(r"toolhead: X:\S+ Y:\S+ Z:(-?[\d.]+)", text)[-1]),
            int(re.findall(r"mcu: .*stepper_z:(-?\d+)", text)[-1]))


def status(obj, field):
    return get("/printer/objects/query?%s=%s" % (obj, field))["status"][obj][field]


def prompt_fail(reason):
    # RESPOND MSG is double quoted: keep double quotes and | out of the text
    reason = reason.replace('"', "'").replace("|", "/")
    lines = ["action:prompt_begin Probe check failed", "action:prompt_text " + reason]
    lines += ["action:prompt_text " + t for t in FAIL_TEXT]
    lines += ["action:prompt_footer_button OK|RESPOND TYPE=command MSG=action:prompt_end|error",
              "action:prompt_show"]
    gcode("\n".join('RESPOND TYPE=command MSG="%s"' % l for l in lines))


def main():
    state = status("print_stats", "state")
    if state in ("printing", "paused"):
        reason = "Printer is %s: run the probe check when it is idle." % state
        if "--json" in sys.argv:
            print(json.dumps({"ok": False, "reason": reason, "fix": []}), flush=True)
        sys.exit(reason)
    bed = get("/printer/objects/query?heater_bed")["status"]["heater_bed"]
    print("Bed %.0f °C, target %.0f (a heating bed caused a miss in Run 23)" % (
        bed["temperature"], bed["target"]), flush=True)
    cfg = status("configfile", "settings")["stepper_z"]
    spm = cfg["microsteps"] * cfg.get("full_steps_per_rotation", 200) / cfg["rotation_distance"]
    t0 = time.time()
    results, err = [], gcode("_PROBE_HOT\nG28\nG90\nG0 X133 Y185 F6000")
    if err:
        results.append((0, 0.0, 0.0, "first home: " + err))
    for h in HEIGHTS if not err else []:
        p0 = pos()
        err = gcode("G0 Z%d %s" % (h, LIFT))
        p1 = pos()
        sign = 1 if (p1[1] - p0[1]) * (p1[0] - p0[0]) > 0 else -1  # stepper count direction vs +Z
        err = err or gcode("G28 Z")
        shift = 0.0 if err else shift_mm(p1, pos(), spm, sign)
        if not err and abs(shift) <= LIMIT_MM:
            err = gcode("PROBE")
        z = float(status("probe", "last_z_result")) if not err and abs(shift) <= LIMIT_MM else 0.0
        results.append((h, z, shift, err))
        print("    Z %d: %s" % (h, err or "zero moved %+.3f mm, probe %.3f" % (shift, z)), flush=True)
        if not judge(results)[0]:
            break  # a miss leaves Z unhomed; a mid-air home would climb further each round
    ok, reason = judge(results)
    if ok:
        gcode("G0 Z10 %s" % LIFT)
    gcode("M104 S0")
    print("%s in %d s: %s" % ("PASS" if ok else "FAIL", time.time() - t0, reason), flush=True)
    if "--json" in sys.argv:
        print(json.dumps({"ok": ok, "reason": reason, "fix": [] if ok else FAIL_TEXT}), flush=True)
    elif ok:
        print("Only a pass if you saw the nozzle touch the bed on the first home.", flush=True)
        gcode('RESPOND MSG="Probe check passed: %s"' % reason)
    else:
        prompt_fail(reason)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
