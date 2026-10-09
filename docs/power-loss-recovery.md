# Power loss recovery: design (software only)

**Status:** design for review (D-098), nothing built yet · **Date:** 2026-10-08 · **Printer:** StarStack S1

## What the user asked for
- Resume a print after a power cut. **Very short outages resume by themselves.**
- No extra hardware for now: the FLY Micro4 has no power-detect input, and Mellow's own
  `[power_resume]` only runs on their FLY hosts with FLYOS-Fast (not on the CB1).
  A detection signal (KPPM or a mains detector) can be added later; it would add a clean
  retract/lift and an exact position at the moment of the cut (see "Later: with hardware").
- **Nothing moves until the bed and the nozzle are back at temperature.** Then Z lifts, then X/Y
  re-home, then the head goes back and the print continues (user, 2026-10-08).
- Short outage = the bed is still within 10 °C of its target when Klipper is back (the CB1 has no
  clock that survives a power cut, and a still-hot bed also means the part is still stuck down).
- Longer outage: the screen asks, with a warning to check the part (Resume / Discard).
- On resume: straight back to the part (no brush wipe). Lift 2 mm (user).
- Z can be trusted after a power cut: the S1's gantry holds its height with the motors off (user).

## What can't be done without hardware (agreed)
- Nothing runs at the moment of the cut: no retract, no lift. The nozzle sits on the part while it
  cools, so expect a small mark there.
- The resume point is the last checkpoint (at most `interval` seconds old, default 2 s). The
  printer re-prints that short stretch over plastic that is already there: a small ridge.
- The CB1 loses power without shutting down: a small risk of SD-card damage on any outage. The
  checkpoint itself is written safely (new file, flush to disk, rename).
- Z after a power cycle can be off by up to about 2 full steps (±0.08 mm on the S1's 8 mm lead) when
  the Z motor switches back on.

## Parts

### 1. Checkpoint service (new: `recovery/starstack-recovery.py`, systemd unit, installed by install.sh)
Runs on the CB1 beside Klipper and talks to Moonraker only (it never touches Klipper's command queue,
so it can't slow or disturb a print). While a print is running it saves a checkpoint:
- every **2 s** (`interval`), and at every layer change;
- to `/var/lib/starstack/print-checkpoint.json`: write a temp file, `fsync`, rename, `fsync` the
  folder (a cut mid-write leaves the previous checkpoint intact).

Contents:
| Field | From | Used for |
|---|---|---|
| file, file size + modified time | `print_stats.filename`, Moonraker file info | refuse to resume a file that changed |
| `file_position` | `virtual_sdcard.file_position` (read ahead of the moves) | where to search for the resume line |
| `live_position` X Y Z E | `motion_report.live_position` (where the head physically is) | the exact resume point and Z |
| layer, total layers | `print_stats.info` | screen text |
| bed / nozzle targets | `heater_bed.target`, `extruder.target` | reheat |
| part fan | `fan.speed` | restore |
| speed %, flow %, PA, smooth time | `gcode_move`, `extruder` | restore |
| absolute/relative XYZ and E, G92 offsets, Z offset | `gcode_move` | restore |
| bed mesh points + settings | `bed_mesh` (when the mesh changes) | restore (see 4) |
| canceled parts | `exclude_object.excluded_objects` | restore |
| `active: true` | | cleared when the print ends normally (done / canceled / error) |

SD-card wear: about 1 KB every 2 s (7,200 small writes on a 4 h print). Acceptable, but `interval`
is a setting; 5 s halves it at the cost of a longer re-printed stretch.

### 2. Finding the exact resume line
`file_position` is read ahead of the moves, so the line the head was on at checkpoint time is a
little earlier. The service reads the file backwards from `file_position` and finds the move whose
path passes through the checkpoint's `live_position` X/Y on the same layer (within 0.1 mm). The resume
starts at that point of that move (the rest of the move is printed, then the file continues).
If no move matches (strange file), it falls back to the start of that line and says so.

### 3. Detecting a power cut
When the CB1 boots and Klipper is ready, a checkpoint with `active: true` means the print never
finished, so the power was cut (or the CB1 crashed: see crash detection, next question round).
Klipper itself starts with no print, so nothing moves on its own.

### 4. The bed mesh after a reboot
The mesh measured at the start of the print is lost when Klipper restarts. The service writes it as a
Klipper mesh profile `[bed_mesh ss_resume]` into `starstack_resume.cfg` whenever the mesh changes;
printer.cfg includes `starstack_resume*.cfg` (a pattern, so a missing file is fine). After the reboot
the recovery loads it with `BED_MESH_PROFILE LOAD=ss_resume`. No probing with parts on the bed.

### 5. Resume (macros `_SS_RECOVER_*`, driven step by step like PRINT_START's 1 s timer)
1. **Heat, no movement**: bed and nozzle to the saved targets (the nozzle may be stuck in the
   plastic; it must be soft before anything moves). Part fan off. Wait until both are within 2 °C.
   Cancel/Don't resume works at any time. Heating time limit: the same 10 min as PRINT_START.
2. **Lift Z**: tell Klipper Z is at the saved physical height (`SET_KINEMATIC_POSITION`, the only
   way to use Z without homing it onto the part) and raise **2 mm**.
3. **Re-home X and Y** (sensorless, the head is above the part). The S1's `[homing_override]` lifts
   Z by 3 mm before homing; the recovery accounts for that (Z is set again afterwards from the known
   height + 2 + 3 mm).
4. Restore the state: load `ss_resume` mesh, offsets, absolute/relative modes, `G92 E`, speed and
   flow %, PA, fan, canceled parts (the file's `EXCLUDE_OBJECT_DEFINE` lines are re-run from its start
   first, then `EXCLUDE_OBJECT` for each canceled part).
5. **Go back**: move above the resume point, lower to the print height, then continue the file from
   the resume line (`M23` file, `M26` byte offset, `M24`). No purge or wipe (user: straight back).
6. The checkpoint stays `active` (with the new job) until the print ends normally, so a second cut
   during the same print also resumes.

**Safety note:** `SET_KINEMATIC_POSITION` is on the macro safety review's "never used" list. It is
needed here (Z can't be homed with a part on the bed) and is limited to: only from the recovery, only
with a checkpoint for the same file, only after both heaters are at temperature, and only for Z
(X/Y are always homed for real). The safety review gets a new section for it before this ships.

### 6. Screen and Mainsail
Shown on the touchscreen Home page and as a Mainsail prompt (same text, same buttons):

**Short outage (bed still within 10 °C): resumes by itself**
> **Power cut: resuming Main(27)**
> 47 % · layer 82 / 175
> Heating bed 76 / 80° · nozzle 140 / 240°. Nothing moves until both are hot.
> [ Don't resume ]

**Longer outage (bed cooled)**
> **Print stopped by a power cut**
> Main(27) · 47 % · layer 82 / 175
> Check the part is still stuck to the bed before resuming.
> [ Discard ] [ Resume ]

After **Discard**: the checkpoint is cleared and the screen offers *Print again* (from the start).
Mainsail's console logs every step ("Power cut recovery: heating", "lifting Z", "homing X/Y",
"resuming at line …").

## Tests (S1, bench approval)
1. Checkpoint only: print, watch the file update every 2 s; end normally → `active` cleared.
2. Resume line: compare the found line with the printed position on 20 checkpoints (offline).
3. Short outage: pull the plug mid-print for 5 s → auto-resume, no movement before both are hot,
   Z lift → X/Y home → continue. Look at the seam.
4. Long outage: unplug until the bed is below 70 °C → question → Resume; then again → Discard.
5. Canceled part before the cut stays canceled; mesh restored (compare `BED_MESH_OUTPUT`).
6. Second cut in the same print.
7. A changed or deleted file → refuses with a message.

## Later: with hardware
A power-fail signal (KPPM on the CB1 or a mains detector on a FLY Micro4 input) lets Klipper act at
the moment of the cut: heaters off, stop the file, retract 1 mm, lift 2 mm, save the exact line. That
removes the mark and the re-printed stretch; the resume half of this design stays the same.
