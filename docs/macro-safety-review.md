# Macro Safety Review: `macros/starstack_macros.cfg` v1.1

**Date:** 2026-10-04 · **Reviewer:** Claude (for user sign-off) · **Status:** approved and released; on the S1 since 2026-10-08. Updated 2026-10-08 for the S1 filament values (D-081) and the S1's own macros (below); v1.1 adds `PRINT_START` (D-089)

## Global checks

| Check | Result | Evidence |
|---|---|---|
| No macro changes `max_temp`, `min_temp`, `min_extrude_temp`, `verify_heater`, endstops or kinematics | ✅ | The file contains no `SET_HEATER`/`verify`/`SET_KINEMATIC_POSITION`/`FORCE_MOVE`/`SET_STEPPER_ENABLE`/`SET_VELOCITY_LIMIT` |
| Highest temperature any macro requests | ✅ 240 °C nozzle / 80 °C bed | `_SS.materials`. Klipper rejects anything above `max_temp` anyway |
| No blocking heat waits (M109, M190, TEMPERATURE_WAIT) | ✅ | Cold nozzle → start heating + message, never a stuck queue. `PRINT_START` waits with the file paused and a 1 s timer, so Cancel always runs at once (D-089) |
| Heater that never gets to temperature | ✅ | Each `PRINT_START` heating step has 10 min (`start_heat_timeout`), then the print is canceled with a message. Klipper's `verify_heater` still catches real faults sooner |
| Macro names Klipper can call | ✅ | `check_macros.py` rejects names like `_S1_X` (letters then a digit), which Klipper reads as command `_S1` (D-089) |
| Cold extrusion | ✅ | `LOAD`/`UNLOAD` only extrude when within 5 °C of target. `PURGE_MORE` checks `can_extrude`. Klipper's `min_extrude_temp` still applies underneath |
| Filament moves while printing | ✅ blocked | `print_stats.state == 'printing'` → error. Allowed when **paused** (runout / colour change) |
| Heater left on after an abandoned filament change | ✅ | `_SS_FIL_TIMEOUT` turns the nozzle off after 300 s unless printing/paused. `FILAMENT_DONE` and `COOL_DOWN` cancel it. `[idle_timeout]` is a second layer |
| Max extrude length per move | ✅ 100 mm | Unload 100 mm, load 50 + purge 60 (two moves). Below `max_extrude_only_distance` (S1: 500, bench: 150) |
| Flow limits | ✅ 40–120 % | `SET_FLOW` clamps. `FLOW_ADJUST` goes through `SET_FLOW` |
| Speed presets | ✅ | `M220` only (50/100/125/150 %). Klipper's `max_velocity`/`max_accel` still cap the real speed |
| Preheat / cool down during a print | ✅ blocked | Prevents a mis-tap from changing or killing a running print (use Tune instead) |
| G-code state left changed | ✅ | Every extrude is wrapped in `SAVE_GCODE_STATE`/`RESTORE_GCODE_STATE` (relative E mode doesn't leak into prints) |
| Runout | ✅ | `pause_on_runout` pauses first (Klipper), then `_SS_RUNOUT` records "NONE" loaded and shows a message |

## Per macro

| Macro | Button | What it can do | Risk | Mitigation |
|---|---|---|---|---|
| `SPEED_SILENT/NORMAL/FAST/DRAFT` | Speed chips | M220 50–150 % | Low | Machine limits still apply |
| `SET_FLOW`, `FLOW_ADJUST` | Flow ±1/±5 | M221 | Low | Clamped 40–120 % |
| `PREHEAT[_PLA/_PETG/_TPU]` | Preheat | M104/M140 ≤ 240/80 (TPU bed 50, D-082) | Low | Blocked while printing. idle_timeout |
| `COOL_DOWN` | Cool down | Heaters + fan off | Low | Blocked while printing |
| `LOAD_FILAMENT` | Load | Heat + 110 mm extrude (50 + 60 purge) | Medium | Temperature gate, state gate, timeout |
| `PURGE_MORE` | Purge more | 60 mm extrude | Low | `can_extrude`, state gate |
| `UNLOAD_FILAMENT` | Unload | Heat + 100 mm retract | Medium | Temperature gate, state gate, timeout |
| `FILAMENT_DONE` | Done | Nozzle heater off (unless paused) | Low | — |
| `_SS_RUNOUT` | (sensor) | Records state, message | Low | Klipper already paused |
| `PRINT_START` (+ `_SS_START_STEP`, `_SS_START_MESH`, `_SS_START_TICK`) | Slicer start G-code | Bed/nozzle to the slicer's temperatures, home, `NOZZLE_CLEAN WAIT=0`, bed mesh, park at X0 Y0 Z15 | Medium | Only runs inside a print file. Needs both temperatures (else the print stops with an error). Pauses with `PAUSE_BASE` (no moves); resumes in place (`PAUSE_STATE` re-saved, so no move back to the pre-homing position). Time limit per heating step. Cancel works at any step |
| `_SS_RESUME_GUARD` | RESUME (via the printer's resume macro) | Refuses RESUME while `PRINT_START` is getting ready | Low | Stops a resume into an unhomed, cold start |
| `M600` | (slicer color change) | Calls Mainsail's `PAUSE` (retract + park) | Low | No heating or extrusion of its own. Ignored if already paused. Resume reheats via the UI or Mainsail's RESUME |

## Things to tune/verify on the real printer (Phase 3.5)
- ✅ `load_mm` 50, `purge_mm` 60, `unload_mm` 100: the values from the S1's old working macros (D-081).
- ✅ `max_extrude_only_distance` 500 in the S1 config.
- TPU load speed (120 mm/min): not tried with TPU yet.

## S1 printer.cfg macros (`config/s1/printer.cfg`, D-081)

These live in the printer config, not in the StarStack macros, because they are specific to the S1's hardware.
`NOZZLE_CLEAN` may wait for heat (`M109`) when run by hand; `PRINT_START` calls it with `WAIT=0` and waits without blocking.

| Macro | Called by | What it can do | Risk | Mitigation |
|---|---|---|---|---|
| `[homing_override]` | G28 | Lift 3 mm, sensorless X/Y, move to X133 Y185, Z on the PZ probe | Medium | User's working macro, unchanged. Z motor current lowered while probing (probe `activate_gcode`) |
| `NOZZLE_CLEAN` | `PRINT_START` (`WAIT=0`), or by hand | Wipe on the brush at Z 1.2, re-home Z, park at Z 0, wait for 150 °C (not with `WAIT=0`) | Medium | User's working macro; only the `WAIT` option added (D-089). Homes first if needed. Brush position confirmed by the user |
| `_CLIENT_VARIABLE` | Mainsail PAUSE/RESUME/CANCEL | Park X0 Y180, lift 10 mm | Low | Mainsail's own macros, inside the axis limits |
| `_PRINTER_PAUSE_FAN` / `_PRINTER_RESUME_FAN` | PAUSE / RESUME | Part fan off / back on; resume first runs `_SS_RESUME_GUARD` | Low | Were `_S1_…`, which never ran (Klipper read them as `_S1`, D-089) |
| `_PRINTER_CANCEL_LIFT` | CANCEL_PRINT | Lift up to 40 mm, never past Z max | Low | Only when Z is homed |
| `[idle_timeout]` | 15 min idle | Paused: nozzle off only. Otherwise heaters and motors off. Does nothing while `PRINT_START` is getting ready | Low | Keeps the print in place while paused. `PRINT_START` has its own time limits |
| `CHANGE_FILAMENT` | Slicer change filament G-code | Same as `M600` | Low | — |

Config limits changed: `min_temp` -50 → 0 on nozzle and bed (stricter: a broken sensor now stops the printer).
Nothing loosened.

## Bench limits
The bench heaters are fake (Pi CPU temperature, ~40 °C), so on the bench we can test: the speed and flow macros, preheat/cool-down targets, every refusal path (cold, printing, unknown material), the timeout, and the remembered-material variable. The actual extrusion paths can only run on the real printer.
