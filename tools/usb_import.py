#!/usr/bin/env python3
"""Copy new G-code files from a mounted USB stick into the print jobs folder (D-065).

    python3 tools/usb_import.py <stick mount point> [--gcodes ~/printer_data/gcodes]

Run as the printer user by usb/usb_import.sh (which mounts the stick read-only and unmounts it after).
- Keeps the stick's folders. Hidden files/folders and system folders are skipped.
- A file already on the printer with the same content (at its name or a "name (n)" copy) is skipped.
- Same name, different content: saved as "name (2).gcode", "name (3).gcode", ...
- Copies to a hidden temp name first, so Moonraker never sees a half-copied file.
- Writes <gcodes>/.starstack/usb_import.json; the touchscreen watches it and asks
  "Print this one now?" for the newest copied file.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time

EXTS = (".gcode", ".gco", ".g")
SKIP_DIRS = {"System Volume Information", "$RECYCLE.BIN", "LOST.DIR", "lost+found"}
FREE_MARGIN = 200 * 1024 * 1024  # never fill the SD card / eMMC completely


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def candidates(dest):
    """dest, then 'stem (2).ext', 'stem (3).ext', ..."""
    yield dest
    stem, ext = os.path.splitext(dest)
    n = 2
    while True:
        yield f"{stem} ({n}){ext}"
        n += 1


def place(src, dest):
    """Return (target path, already_there). target is None when the content is already present."""
    size, src_hash = os.path.getsize(src), None
    for cand in candidates(dest):
        if not os.path.exists(cand):
            return cand, False
        if os.path.getsize(cand) == size:
            src_hash = src_hash or digest(src)
            if digest(cand) == src_hash:
                return None, True


def stick_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS)
        for name in sorted(filenames):
            if not name.startswith(".") and name.lower().endswith(EXTS):
                yield os.path.join(dirpath, name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stick")
    ap.add_argument("--gcodes", default=os.path.expanduser("~/printer_data/gcodes"))
    args = ap.parse_args()
    stick, gcodes = os.path.abspath(args.stick), os.path.abspath(args.gcodes)
    copied, skipped, failed = [], 0, []
    for src in stick_files(stick):
        rel = os.path.relpath(src, stick)
        target, present = place(src, os.path.join(gcodes, rel))
        if present:
            skipped += 1
            continue
        size = os.path.getsize(src)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if shutil.disk_usage(os.path.dirname(target)).free < size + FREE_MARGIN:
            failed.append({"file": rel, "reason": "not enough space"})
            continue
        tmp = os.path.join(os.path.dirname(target), "." + os.path.basename(target) + ".part")
        try:
            shutil.copyfile(src, tmp)  # new modification time: copied files count as newest
            os.replace(tmp, target)
        except OSError as e:
            failed.append({"file": rel, "reason": str(e)})
            if os.path.exists(tmp):
                os.remove(tmp)
            continue
        copied.append((os.path.getmtime(src), os.path.relpath(target, gcodes).replace(os.sep, "/")))
        print(f"copied: {rel} -> {copied[-1][1]}")
    newest = max(copied)[1] if copied else None  # newest by the stick's file time
    report = {
        "time": time.time(),
        "copied": [p for _t, p in sorted(copied, reverse=True)],
        "newest": newest,
        "skipped": skipped,
        "failed": failed,
    }
    state_dir = os.path.join(gcodes, ".starstack")
    os.makedirs(state_dir, exist_ok=True)
    tmp = os.path.join(state_dir, ".usb_import.json.part")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    os.replace(tmp, os.path.join(state_dir, "usb_import.json"))
    print(f"USB import: {len(copied)} copied, {skipped} already on the printer, {len(failed)} failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
