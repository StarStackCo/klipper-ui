"""Extruder load test (D-120, B-16): can the TMC2209 StallGuard reading (SG_RESULT) tell filament,
no filament and a jam apart? Extrudes at rising flow and reads SG_RESULT during each move.
Lower SG_RESULT = more load. Needs a hot nozzle and an idle printer. Run from the PC:
    python tools/sg_test.py LABEL [--host 192.168.0.102] [--flows 2,5,8,12,16,20]
The extruder is put in StealthChop for the test; restart Klipper afterwards to undo that.
Results are added to docs/data/sg_test.json."""
import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request

AREA = 3.14159 * 0.875**2  # mm² of 1.75 mm filament
SECONDS = 4  # each flow step


def call(host, path, body=None):
    url = f"http://{host}:7125{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["result"]


def gcode(host, script, show=True):
    if show:
        print(f"  > {script}")
    out = call(host, "/printer/gcode/script", {"script": script})
    if show:
        print(f"  < {out}")


def sg(host):
    since = time.time()
    gcode(host, "DUMP_TMC STEPPER=extruder REGISTER=SG_RESULT", show=False)
    for line in call(host, "/server/gcode_store?count=5")["gcode_store"]:
        m = re.search(r"sg_result=(\d+)", line["message"])
        if m and line["time"] >= since - 1:
            return int(m.group(1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label", help="e.g. pla-loaded, no-filament, pla-held")
    ap.add_argument("--host", default="192.168.0.102")
    ap.add_argument("--flows", default="2,5,8,12,16,20", help="mm³/s")
    a = ap.parse_args()
    q = "/printer/objects/query?" + urllib.parse.quote("print_stats&extruder")
    st = call(a.host, q)["status"]
    print(f"state {st['print_stats']['state']}, nozzle {st['extruder']['temperature']:.0f}°C")
    if st["print_stats"]["state"] in ("printing", "paused"):
        raise SystemExit("printer busy: not testing")
    if st["extruder"]["temperature"] < 180:
        raise SystemExit("nozzle below 180°C: heat it first")
    for field, value in (("en_spreadcycle", 0), ("tpwmthrs", 0), ("tcoolthrs", 0xFFFFF)):
        gcode(a.host, f"SET_TMC_FIELD STEPPER=extruder FIELD={field} VALUE={value}")
    gcode(a.host, "M83")
    rows = []
    for flow in [float(f) for f in a.flows.split(",")]:
        speed = flow / AREA  # mm/s of filament
        gcode(a.host, f"G1 E{speed * SECONDS:.1f} F{speed * 60:.0f}")
        end = time.time() + SECONDS
        time.sleep(0.6)  # past the speed-up
        reads = []
        while time.time() < end - 0.3:
            v = sg(a.host)
            if v is not None:
                reads.append(v)
        gcode(a.host, "M400", show=False)
        avg = round(sum(reads) / len(reads)) if reads else None
        print(f"  {flow:>5} mm³/s ({speed:4.1f} mm/s): SG_RESULT {reads} avg {avg}")
        rows.append({"flow": flow, "reads": reads, "avg": avg})
    gcode(a.host, "G1 E-1 F1800")
    path = os.path.join(os.path.dirname(__file__), "..", "docs", "data", "sg_test.json")
    data = json.load(open(path)) if os.path.exists(path) else []
    data.append({"label": a.label, "time": time.strftime("%Y-%m-%d %H:%M"), "steps": rows})
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
    print(f"saved to {os.path.normpath(path)}. Restart Klipper when done testing.")


if __name__ == "__main__":
    main()
