---
name: print-job
description: Slice a model for the StarStack S1 with OrcaSlicer, check the G-code, upload it, queue it or start it. Use whenever a chat on this computer is asked to slice, print, send to the printer, queue or reprint something on the S1 (192.168.0.102, starstack-s1.local), even when the request is about another project (e.g. "print the Saber parts").
---

# Printing on the StarStack S1

Source of this skill: `C:\Users\Sam\Documents\klipper-ui\.claude\skills\print-job\SKILL.md`
(a copy lives in `~/.claude/skills/print-job/` so every chat on this computer finds it). Decisions:
`klipper-ui/docs/DECISIONS.md` D-089 (start G-code), D-106 (checks), D-107 (Orca profile), D-111
(job queue).

## Why this matters
The S1's start of print is the `PRINT_START` macro: filament and nozzle checks, heat soak, nozzle
clean, bed mesh with error handling, layer-shift logging. It only runs if the file was sliced with
the StarStack Orca profile. On 2026-11-03 a chat sliced two Saber files with a `machine.json` it
wrote itself (named "StarStack S1", but with a generic start G-code): they heated with plain
`M190`/`M104` and skipped every check. **Never write or edit printer, process or filament JSON by
hand, and never use an `.orca_printer` from Downloads. Use the repo profile.**

## Rules
- **Ask before starting a print, every time.** Say the file, material, time and plate, and wait for
  a yes. The user must confirm **the plate is clear** and **which filament is loaded**.
- Uploading without starting is fine when the user asked for the file to be on the printer.
- Downloads of models need the user's permission (file, source, size), per chat.
- Show every SSH command and reply (`klipper-ui/scripts/pi.sh '<cmd>'` logs them).
- Home network only; never handle passwords or keys.

## 1. Slice with the repo profile
Orca: `C:\Program Files\OrcaSlicer\orca-slicer.exe` (2.4.2). Profile: `klipper-ui/config/s1/orca/`
(processes: `0.10mm Detail`, `0.20mm Balanced`, `0.20mm Strength`, `0.25mm Draft`; filaments:
`PLA`, `PETG`, `Hatchbox PLA`, `Hatchbox PETG`, `Overture PLA`, `Overture MATTE PLA`, `Silk PLA`,
`95A TPU`).

```bash
W="$TEMP/orcat/job1"   # short path: Orca fails on long Windows paths
python C:/Users/Sam/Documents/klipper-ui/tools/orca_profile.py cli "$W" "0.20mm Balanced" "PLA" "High Temp Plate"
"/c/Program Files/OrcaSlicer/orca-slicer.exe" --slice 0 --arrange 1 \
  --load-settings "$W/machine.json;$W/process.json" --load-filaments "$W/filament.json" \
  --outputdir "$W/out" model1.stl model2.stl
```
Gotchas (Orca 2.4.2 CLI):
- `--scale` errors: scale the STL yourself first (e.g. a model exported in meters needs ×1000).
- Some 3MF files crash the CLI: extract the meshes to STL and slice those.
- No thumbnails are made from the command line (the screen shows a file icon). Fine.
- Multi-color or multi-filament jobs: one `--load-filaments` entry per filament, `;`-separated.
- Check the plate fits (220×220 bed) and objects don't touch; `--arrange 1` places them.

## 2. Check the G-code (must say OK)
```bash
python C:/Users/Sam/Documents/klipper-ui/tools/orca_profile.py check "$W/out/plate_1.gcode"
```
It needs a `PRINT_START ... MATERIAL= NOZZLE= PRINTER="StarStack S1"` line and the printer preset
"StarStack S1". NOT OK means slice again with step 1; never patch the G-code by hand.
Rename the file to something readable (`<name> <material>.gcode`, e.g. `Saber hilt PETG.gcode`).

## 3. Look at the printer
```bash
curl -s "http://192.168.0.102:7125/printer/objects/query?print_stats=state,filename&save_variables"
curl -s http://192.168.0.102:7125/server/job_queue/status
```
- `print_stats.state`: `printing`/`paused` = busy; `complete`/`cancelled`/`standby` = free (but the
  plate may still hold the last print).
- `save_variables.variables.loaded_material`: the filament the printer thinks is loaded. If it
  differs from the file's, tell the user (the printer will also stop and ask).

## 4. Upload, then queue or start
Upload only (always safe):
```bash
curl -s -F "file=@$W/out/Saber hilt PETG.gcode" http://192.168.0.102:7125/server/files/upload
```
- **Printer busy and the user wants it next:** add it to the queue. It never starts by itself; the
  touchscreen asks "Plate is clear, start" when the current print ends (D-111).
  `curl -s -X POST "http://192.168.0.102:7125/server/job_queue/job?filenames=Saber%20hilt%20PETG.gcode"`
- **Printer free, the user said start, plate clear, right filament:**
  `curl -s -X POST "http://192.168.0.102:7125/printer/print/start?filename=Saber%20hilt%20PETG.gcode"`
- Don't use `print=true` on the upload: on a free printer it starts at once, without the
  questions above.
- The queue lives in Moonraker's memory: a Moonraker restart or power cut empties it.

## 5. After starting
Report the file, the estimated time and that `PRINT_START` is running (`gcode_macro PRINT_START`
`stage` goes filament → material → bed → nozzle → home → clean → cool → soak → mesh → final, then
empty). If the print stops at the start, the touchscreen shows why (error card, D-105).
