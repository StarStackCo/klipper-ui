#!/usr/bin/env python3
"""Bench tests for macros/starstack_macros.cfg.
Runs ON THE PI (via: scripts/pi.sh 'python3 -' < scripts/bench_test_macros.py).
Talks to Moonraker on localhost. Bench v2.1 only: fake heaters, no motors attached.
Prints every G-code sent, Klipper's replies, and PASS/FAIL per check."""
import json, time, urllib.request, urllib.parse

API = "http://localhost:7125"
results = []


def get(path):
    with urllib.request.urlopen(API + path, timeout=30) as r:
        return json.load(r)["result"]


def post(path):
    req = urllib.request.Request(API + path, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r).get("result")
    except urllib.error.HTTPError as e:
        return "HTTP %s: %s" % (e.code, json.load(e).get("error", {}).get("message", ""))


def gcode(script):
    t0 = time.time() - 0.2
    print("\n>>> G-CODE: " + script.replace("\n", " | "))
    res = post("/printer/gcode/script?script=" + urllib.parse.quote(script))
    time.sleep(0.4)
    msgs = [m["message"] for m in get("/server/gcode_store?count=30")["gcode_store"]
            if m["time"] >= t0 and m["type"] == "response"]
    for m in msgs:
        print("    <<< " + m)
    if res != "ok":
        print("    <<< (api) " + str(res))
    return msgs, res


def status():
    q = "extruder&heater_bed&fan&gcode_move&save_variables&print_stats"
    return get("/printer/objects/query?" + q)["status"]


def check(name, ok, detail=""):
    results.append((name, ok))
    print("    [%s] %s %s" % ("PASS" if ok else "FAIL", name, detail))


def has(msgs, text):
    return any(text.lower() in m.lower() for m in msgs)


print("=== StarStack macro bench tests ===")
print("printer state:", get("/printer/info")["state"])
st = get("/printer/objects/query?pause_resume&filament_switch_sensor%20runout")["status"]
check("runout sensor disabled on bench", st["filament_switch_sensor runout"]["enabled"] is False)
if st["pause_resume"]["is_paused"]:
    gcode("CLEAR_PAUSE")

# 1. Speed presets
for macro, f in [("SPEED_SILENT", 0.5), ("SPEED_FAST", 1.25), ("SPEED_DRAFT", 1.5), ("SPEED_NORMAL", 1.0)]:
    gcode(macro)
    sf = status()["gcode_move"]["speed_factor"]
    check(macro + " sets speed factor", abs(sf - f) < 1e-6, "(speed_factor=%s)" % sf)

# 2. Flow + limits
def flow():
    return round(status()["gcode_move"]["extrude_factor"] * 100)
gcode("SET_FLOW PERCENT=100"); check("SET_FLOW 100", flow() == 100, "(%s%%)" % flow())
gcode("FLOW_ADJUST DELTA=1"); check("FLOW_ADJUST +1", flow() == 101, "(%s%%)" % flow())
gcode("FLOW_ADJUST DELTA=-5"); check("FLOW_ADJUST -5", flow() == 96, "(%s%%)" % flow())
m, _ = gcode("SET_FLOW PERCENT=200"); check("SET_FLOW 200 clamps to 120 + warns", flow() == 120 and has(m, "limited"), "(%s%%)" % flow())
m, _ = gcode("SET_FLOW PERCENT=10"); check("SET_FLOW 10 clamps to 40 + warns", flow() == 40 and has(m, "limited"), "(%s%%)" % flow())
gcode("SET_FLOW PERCENT=100"); check("flow restored to 100", flow() == 100)

# 3. Preheat / cool down
m, _ = gcode("PREHEAT MATERIAL=ABS"); s = status()
check("PREHEAT unknown material refused, no heat", has(m, "Unknown material") and s["extruder"]["target"] == 0)
gcode("PREHEAT_PLA"); s = status()
check("PREHEAT_PLA → 210/60", s["extruder"]["target"] == 210 and s["heater_bed"]["target"] == 60)
gcode("PREHEAT_TPU"); s = status()
check("PREHEAT_TPU → 225/40", s["extruder"]["target"] == 225 and s["heater_bed"]["target"] == 40)
gcode("M106 S128"); gcode("COOL_DOWN"); s = status()
check("COOL_DOWN → heaters 0, fan 0", s["extruder"]["target"] == 0 and s["heater_bed"]["target"] == 0 and s["fan"]["speed"] == 0)

# 4. Filament (fake heater never gets hot → heating path + refusals)
m, _ = gcode("LOAD_FILAMENT"); check("LOAD without material refused", has(m, "Pick a material") and status()["extruder"]["target"] == 0)
m, _ = gcode("LOAD_FILAMENT MATERIAL=petg"); s = status()
check("LOAD PETG cold → heats to 240, asks to run again, nothing loaded",
      s["extruder"]["target"] == 240 and has(m, "Run Load again") and s["save_variables"]["variables"]["loaded_material"] == "NONE")
m, _ = gcode("PURGE_MORE"); check("PURGE_MORE cold refused", has(m, "too cold"))
m, _ = gcode("FILAMENT_DONE"); check("FILAMENT_DONE → nozzle off", status()["extruder"]["target"] == 0)
m, _ = gcode("UNLOAD_FILAMENT"); check("UNLOAD with nothing recorded refused", has(m, "No filament recorded") and status()["extruder"]["target"] == 0)
gcode("SAVE_VARIABLE VARIABLE=loaded_material VALUE='\"PETG\"'")
m, _ = gcode("UNLOAD_FILAMENT"); check("UNLOAD uses remembered PETG → 240", status()["extruder"]["target"] == 240 and has(m, "unload PETG"))
gcode("FILAMENT_DONE")
gcode("SAVE_VARIABLE VARIABLE=loaded_material VALUE='\"NONE\"'")
check("memory reset to NONE", status()["save_variables"]["variables"]["loaded_material"] == "NONE")

# 5. Abandoned-heater timeout (shortened to 3 s for the test)
gcode("M104 S200\nUPDATE_DELAYED_GCODE ID=_SS_FIL_TIMEOUT DURATION=3")
time.sleep(5)
msgs = [x["message"] for x in get("/server/gcode_store?count=5")["gcode_store"]]
check("timeout turns nozzle off after an abandoned change", status()["extruder"]["target"] == 0 and has(msgs, "left unfinished"))

# 6. Locked while printing: tiny test print (fake homing, no motors attached)
gfile = "ss_bench_test.gcode"
# Many short dwells: Klipper throttles them to real time without holding the
# G-code queue, so test commands can run while the print is really "printing".
body = "; StarStack bench test - fake homing, dwell only\nG28\n" + "G4 P500\n" * 60
boundary = "----ssbench"
data = ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: application/octet-stream\r\n\r\n%s\r\n--%s--\r\n"
        % (boundary, gfile, body, boundary)).encode()
req = urllib.request.Request(API + "/server/files/upload", data=data, method="POST",
                             headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
urllib.request.urlopen(req, timeout=30).read()
print("\n>>> uploaded %s: %r" % (gfile, body))
print(">>> start print:", post("/printer/print/start?filename=" + gfile))
time.sleep(4)
check("test print is printing", status()["print_stats"]["state"] == "printing", "(state=%s)" % status()["print_stats"]["state"])
for cmd, txt in [("PREHEAT_PLA", "off while printing"), ("COOL_DOWN", "while printing"),
                 ("LOAD_FILAMENT MATERIAL=PLA", "locked while printing"), ("UNLOAD_FILAMENT MATERIAL=PLA", "locked while printing"),
                 ("PURGE_MORE", "locked while printing")]:
    m, _ = gcode(cmd)
    check(cmd + " refused while printing", has(m, txt))
gcode("SPEED_FAST"); check("speed preset works while printing", abs(status()["gcode_move"]["speed_factor"] - 1.25) < 1e-6)
gcode("SPEED_NORMAL")
gcode("PAUSE"); time.sleep(2)
check("paused", status()["print_stats"]["state"] == "paused")
m, _ = gcode("LOAD_FILAMENT MATERIAL=PLA")
check("LOAD allowed while paused (heats)", status()["extruder"]["target"] == 210 and has(m, "Run Load again"))
m, _ = gcode("FILAMENT_DONE"); check("FILAMENT_DONE keeps heater on while paused", status()["extruder"]["target"] == 210 and has(m, "kept on"))
gcode("CANCEL_PRINT"); time.sleep(3)
s = status()
check("cancelled, heaters off", s["print_stats"]["state"] in ("cancelled", "standby") and s["extruder"]["target"] == 0, "(state=%s)" % s["print_stats"]["state"])
req = urllib.request.Request(API + "/server/files/gcodes/" + gfile, method="DELETE")
urllib.request.urlopen(req, timeout=30).read()
print(">>> deleted test file", gfile)

print("\n=== SUMMARY: %d/%d passed ===" % (sum(1 for _, ok in results if ok), len(results)))
for n, ok in results:
    if not ok:
        print("FAILED:", n)
print("final printer state:", get("/printer/info")["state"])
