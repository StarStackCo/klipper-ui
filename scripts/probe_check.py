#!/usr/bin/env python3
"""Z homing check for the S1 (D-NEW probe check, B-24).
Runs ON THE PI: scripts/pi.sh 'python3 -' < scripts/probe_check.py
Self-test of the pass/fail logic (any PC): python scripts/probe_check.py --selftest

Nozzle at a steady clean_temp (_PROBE_HOT), then at the homing point X133 Y185 it homes Z from
higher and higher starts (resonance and long descents caused misses and mid-air triggers, D-134,
D-140). After each home a PROBE at 5 mm/s must read the bed at Z 0 within LIMIT_MM: a mid-air
trigger reads below 0, a late one above. Stops at the first failure and shows the user a prompt on
the touchscreen and Mainsail. Uses the configured homing_speed; never runs while printing."""
import json, sys, time, urllib.error, urllib.parse, urllib.request

API = "http://localhost:7125"
HEIGHTS = [5, 10, 20, 40, 80, 120, 160]  # mm; the homing override adds 3, position_max is 165
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
    """results: list of (height, z or None, error or None). Returns (ok, reason)."""
    for h, z, err in results:
        if err:
            return False, "From Z %d: %s" % (h, err)
        if abs(z) > LIMIT_MM:
            kind = "triggered %.2f mm above the bed" % -z if z < 0 else "triggered %.2f mm late" % z
            return False, "From Z %d the probe %s" % (h, kind)
    return True, "Homed from %s mm, probe read %s" % (
        ", ".join(str(h) for h, _, _ in results),
        ", ".join("%.3f" % z for _, z, _ in results))


def selftest():
    assert judge([(5, 0.02, None), (10, -0.03, None)])[0]
    assert not judge([(5, 0.02, None), (10, -0.4, None)])[0]  # mid-air trigger
    assert "above the bed" in judge([(10, -0.4, None)])[1]
    assert "late" in judge([(10, 1.1, None)])[1]
    assert not judge([(40, None, "No trigger on stepper_z after full movement")])[0]
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
        sys.exit("Printer is %s: run the probe check when it is idle." % state)
    bed = get("/printer/objects/query?heater_bed")["status"]["heater_bed"]
    print("Bed %.0f °C, target %.0f (a heating bed caused a miss in Run 23)" % (
        bed["temperature"], bed["target"]), flush=True)
    t0 = time.time()
    results, err = [], gcode("_PROBE_HOT\nG28\nG90\nG0 X133 Y185 F6000")
    if err:
        results.append((0, None, "first home: " + err))
    for h in HEIGHTS if not err else []:
        err = gcode("G0 Z%d %s\nG28 Z" % (h, LIFT)) or gcode("PROBE")
        z = None if err else float(status("probe", "last_z_result"))
        results.append((h, z, err))
        print("    Z %d: %s" % (h, err or "probe %.3f" % z), flush=True)
        if not judge(results)[0]:
            break  # after a miss Z is unhomed and the nozzle may be pressed into the bed
    ok, reason = judge(results)
    if ok:
        gcode("G0 Z10 %s" % LIFT)
    gcode("M104 S0")
    print("%s in %d s: %s" % ("PASS" if ok else "FAIL", time.time() - t0, reason), flush=True)
    if ok:
        gcode('RESPOND MSG="Probe check passed: %s"' % reason)
    else:
        prompt_fail(reason)
        sys.exit(1)


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
