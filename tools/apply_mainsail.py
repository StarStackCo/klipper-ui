#!/usr/bin/env python3
"""Apply (or roll back) StarStack's Mainsail UI settings and macro groups via Moonraker on this Pi.

    python3 tools/apply_mainsail.py            apply mainsail-theme/settings.json + macrogroups.json
    python3 tools/apply_mainsail.py --show     print what is stored now
    python3 tools/apply_mainsail.py --rollback settings back to Mainsail defaults, StarStack macro groups removed

Runs on the printer (Moonraker on localhost:7125). Used by install.sh. Mainsail stores these in
Moonraker's database (namespace "mainsail"), not in files, so they are applied through the API.
"""
import json
import os
import sys
import urllib.request

API = os.environ.get("MOONRAKER", "http://localhost:7125") + "/server/database/item"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS = json.load(open(os.path.join(ROOT, "mainsail-theme", "settings.json"), encoding="utf-8"))["settings"]
GROUPS = json.load(open(os.path.join(ROOT, "mainsail-theme", "macrogroups.json"), encoding="utf-8"))


def post(key, value):
    body = json.dumps({"namespace": "mainsail", "key": key, "value": value}).encode()
    req = urllib.request.Request(API, data=body, method="POST", headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10).read()


def delete(key):
    try:
        urllib.request.urlopen(urllib.request.Request(f"{API}?namespace=mainsail&key={key}", method="DELETE"),
                               timeout=10).read()
    except Exception:
        pass


def get(key):
    try:
        with urllib.request.urlopen(f"{API}?namespace=mainsail&key={key}", timeout=10) as r:
            return json.load(r)["result"]["value"]
    except Exception:
        return None


def group_value(g):
    macros = []
    for i, m in enumerate(g["macros"]):
        m = {"name": m} if isinstance(m, str) else m
        macros.append({"pos": i + 1, "name": m["name"], "color": m.get("color", "group"),
                       "showInStandby": g["showInStandby"], "showInPrinting": g["showInPrinting"],
                       "showInPause": g["showInPause"]})
    keys = ("id", "name", "color", "showInStandby", "showInPrinting", "showInPause")
    return {**{k: g[k] for k in keys}, "macros": macros}


def show():
    for s in SETTINGS:
        print(f"  {s['key']:34} {get(s['key'])!r}")
    macros = get("macros") or {}
    print(f"  {'macros.mode':34} {macros.get('mode')!r}")
    for g in (macros.get("macrogroups") or {}).values():
        print(f"  group {g['name']:9} {', '.join(m['name'] for m in g.get('macros', []))}")


mode = sys.argv[1] if len(sys.argv) > 1 else "--apply"
if mode == "--show":
    show()
elif mode == "--rollback":
    for s in SETTINGS:
        post(s["key"], s["was"])
    for g in GROUPS["groups"]:
        delete("macros.macrogroups." + g["id"])
    post("macros.mode", "simple")
    print("Mainsail settings rolled back")
    show()
else:
    for s in SETTINGS:
        post(s["key"], s["value"])
    post("macros.mode", GROUPS["mode"])
    for g in GROUPS["groups"]:
        post("macros.macrogroups." + g["id"], group_value(g))
    print(f"Mainsail: {len(SETTINGS)} settings and {len(GROUPS['groups'])} macro groups applied")
    show()
