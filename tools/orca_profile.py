#!/usr/bin/env python3
"""StarStack S1 OrcaSlicer profile: self-contained presets in config/s1/orca/ (klipper-ui D-107).

Orca's own export keeps user presets as differences from a parent preset ("inherits"), so a bundle
only works on a PC that has the same parents. This tool makes every preset complete on its own
(inherits = "") and packs them into an importable bundle.

  python tools/orca_profile.py build BUNDLE.orca_printer SLICED.gcode
      Unpack an Orca preset bundle and fill in every inherited setting: the printer and the
      filament/process the G-code was sliced with take the exact values from the G-code's
      CONFIG_BLOCK; other filaments take their parent from Orca's system profiles on this PC.
  python tools/orca_profile.py pack
      Write config/s1/orca/StarStack-S1.orca_printer (File > Import > Import Preset Bundle).
  python tools/orca_profile.py cli DIR
      Write machine/process/filament JSON with "type" for orca-slicer --load-settings into DIR.
"""

import glob
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "config", "s1", "orca")
KINDS = {"printer": "machine", "process": "process", "filament": "filament"}
# Orca's built-in presets: the installed program's copy first (matches its version), then the copy
# Orca keeps in the user folder.
SYSTEM = [
    os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "OrcaSlicer", "resources", "profiles"),
    os.path.join(os.environ.get("APPDATA", ""), "OrcaSlicer", "system"),
]


def system_index():
    idx = {}
    paths = [p for d in SYSTEM for p in glob.glob(os.path.join(d, "**", "*.json"), recursive=True)]
    for path in paths:
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if isinstance(data, dict) and data.get("name"):
            idx.setdefault(data["name"], data)
    return idx


def resolve(name, idx, depth=0):
    """A system preset with all its parents merged in."""
    if depth > 15 or name not in idx:
        raise SystemExit(f"Orca system preset not found on this PC: {name!r}")
    data = idx[name]
    merged = resolve(data["inherits"], idx, depth + 1) if data.get("inherits") else {}
    merged.update(data)
    return merged


def keys_of(kind, idx):
    """All settings Orca's system presets of one kind use, with a sample value each."""
    keys = {}
    for data in idx.values():
        if data.get("type") == kind:
            for k, v in data.items():
                keys.setdefault(k, v)
    for meta in ("name", "inherits", "from", "type", "instantiation", "setting_id", "base_id",
                 "filament_id", "printer_model", "printer_variant", "default_print_profile",
                 "default_filament_profile", "renamed_from", "version"):
        keys.pop(meta, None)
    return keys


def read_block(gcode):
    """CONFIG_BLOCK of an Orca G-code file → {key: raw string}."""
    vals, inside = {}, False
    for line in open(gcode, encoding="utf-8", errors="replace"):
        if line.startswith("; CONFIG_BLOCK_START"):
            inside = True
        elif line.startswith("; CONFIG_BLOCK_END"):
            break
        elif inside and " = " in line:
            k, v = line[2:].rstrip("\n").split(" = ", 1)
            vals.setdefault(k.strip(), v)
    if not vals:
        raise SystemExit(f"no CONFIG_BLOCK in {gcode}")
    return vals


def unescape(s):
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "r": "\r", "t": "\t"}.get(m.group(1), m.group(1)), s)


def convert(raw, like):
    """Raw G-code comment value → the JSON shape Orca uses for the same key (string or list)."""
    if not isinstance(like, list):
        return unescape(raw[1:-1] if raw.startswith('"') and raw.endswith('"') else raw)
    if raw.startswith('"'):  # list of quoted strings, ';'-separated
        return [unescape(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', raw)]
    if raw == "":
        return []
    sample = next((x for x in like if x != ""), "")
    if ";" in raw or not re.fullmatch(r"[-+0-9.x%e]*", str(sample)):
        return [x for x in raw.split(";")] if ";" in raw else [raw]
    return raw.split(",")


def build(bundle, gcode):
    block = read_block(gcode)
    idx = system_index()
    z = zipfile.ZipFile(bundle)
    used = {"printer": block.get("printer_settings_id", "").strip('"'),
            "process": block.get("print_settings_id", "").strip('"'),
            "filament": block.get("filament_settings_id", "").strip('"').split('";"')[0]}
    os.makedirs(OUT, exist_ok=True)
    report = []
    for member in z.namelist():
        folder = member.split("/")[0]
        if folder not in KINDS or not member.endswith(".json"):
            continue
        data = json.loads(z.read(member).decode("utf-8"))
        parent = data.get("inherits") or ""
        full = {}
        if parent in idx:
            full = resolve(parent, idx)
        elif parent and data["name"] != used[folder]:
            raise SystemExit(f"{member}: parent {parent!r} is missing; slice with it to rebuild")
        full.update(data)
        filled = 0
        if data["name"] == used[folder]:  # exact values from the G-code for what it used
            # every setting of this kind that any Orca system preset uses (key → a sample value,
            # which also tells whether Orca stores it as a list)
            schema = {**keys_of(KINDS[folder], idx), **full}
            for key, like in schema.items():
                if key in block and key not in data and key not in ("name", "inherits", "from"):
                    full[key] = convert(block[key], like)
                    filled += 1
        for key in ("instantiation", "setting_id", "base_id"):  # ties to Orca's system presets
            full.pop(key, None)
        full.update({"name": data["name"], "inherits": "", "from": "User"})
        if folder != "printer":  # offered for this printer only (was tied to the old parent preset)
            full.update({"compatible_printers": ["StarStack S1"], "compatible_printers_condition": ""})
        full.pop("type", None)
        path = os.path.join(OUT, folder, data["name"] + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(dict(sorted(full.items())), open(path, "w", encoding="utf-8", newline="\n"),
                  indent=4, ensure_ascii=False)
        report.append(f"{folder:9} {data['name']:22} {len(full):4} settings"
                      + (f" ({filled} from the G-code)" if filled else f" (parent: {parent or 'none'})"))
    print("\n".join(sorted(report)))


def presets():
    for folder in KINDS:
        for path in sorted(glob.glob(os.path.join(OUT, folder, "*.json"))):
            yield folder, path


def pack():
    target = os.path.join(OUT, "StarStack-S1.orca_printer")
    files = list(presets())
    structure = {
        "bundle_id": "StarStack S1",
        "bundle_type": "printer config bundle",
        "printer_preset_name": "StarStack S1",
        "printer_config": [f"printer/{os.path.basename(p)}" for f, p in files if f == "printer"],
        "process_config": [f"process/{os.path.basename(p)}" for f, p in files if f == "process"],
        "filament_config": [f"filament/{os.path.basename(p)}" for f, p in files if f == "filament"],
        "version": "00.00.00.00",
    }
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, path in files:
            info = zipfile.ZipInfo(f"{folder}/{os.path.basename(path)}", (2026, 1, 1, 0, 0, 0))
            z.writestr(info, open(path, encoding="utf-8").read(), zipfile.ZIP_DEFLATED)
        z.writestr(zipfile.ZipInfo("bundle_structure.json", (2026, 1, 1, 0, 0, 0)), json.dumps(structure))
    print(f"wrote {os.path.relpath(target, ROOT)} ({len(files)} presets)")


def cli(dest, process="0.25mm Draft", filament="Hatchbox PETG", plate="High Temp Plate"):
    os.makedirs(dest, exist_ok=True)
    for folder, name, fn in (("printer", "StarStack S1", "machine.json"),
                             ("process", process, "process.json"),
                             ("filament", filament, "filament.json")):
        data = json.load(open(os.path.join(OUT, folder, name + ".json"), encoding="utf-8"))
        data["type"] = KINDS[folder]
        if folder == "printer":
            # orca-slicer --load-settings only accepts a process whose compatible_printers names the
            # printer's system preset; a self-contained printer is its own (Orca 2.3.1 CLI)
            data["from"] = "system"
        if folder == "process":
            data["curr_bed_type"] = plate  # chosen on the plate in the GUI, not stored in a preset
        json.dump(data, open(os.path.join(dest, fn), "w", encoding="utf-8"), indent=1)
    print(f"wrote machine/process/filament JSON for {process} + {filament} into {dest}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build" and len(sys.argv) == 4:
        build(sys.argv[2], sys.argv[3])
    elif cmd == "pack":
        pack()
    elif cmd == "cli" and len(sys.argv) >= 3:
        cli(*sys.argv[2:])
    else:
        print(__doc__)
