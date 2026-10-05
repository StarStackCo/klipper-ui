# Macro Safety Review: `macros/starstack_macros.cfg` v1

**Date:** 2026-10-04 · **Reviewer:** Claude (for user sign-off) · **Status:** waiting for approval to deploy to the bench

## Global checks

| Check | Result | Evidence |
|---|---|---|
| No macro changes `max_temp`, `min_temp`, `min_extrude_temp`, `verify_heater`, endstops or kinematics | ✅ | The file contains no `SET_HEATER`/`verify`/`SET_KINEMATIC_POSITION`/`FORCE_MOVE`/`SET_STEPPER_ENABLE`/`SET_VELOCITY_LIMIT` |
| Highest temperature any macro requests | ✅ 240 °C nozzle / 80 °C bed | `_SS.materials`. Klipper rejects anything above `max_temp` anyway |
| No blocking heat waits (M109, M190, TEMPERATURE_WAIT) | ✅ | Cold nozzle → start heating + message, never a stuck queue |
| Cold extrusion | ✅ | `LOAD`/`UNLOAD` only extrude when within 5 °C of target. `PURGE_MORE` checks `can_extrude`. Klipper's `min_extrude_temp` still applies underneath |
| Filament moves while printing | ✅ blocked | `print_stats.state == 'printing'` → error. Allowed when **paused** (runout / colour change) |
| Heater left on after an abandoned filament change | ✅ | `_SS_FIL_TIMEOUT` turns the nozzle off after 300 s unless printing/paused. `FILAMENT_DONE` and `COOL_DOWN` cancel it. `[idle_timeout]` is a second layer |
| Max extrude length per move | ✅ 80 mm | Below `max_extrude_only_distance` (bench 150). **The real config must allow ≥ 80** |
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
| `PREHEAT[_PLA/_PETG/_TPU]` | Preheat | M104/M140 ≤ 240/80 | Low | Blocked while printing. idle_timeout |
| `COOL_DOWN` | Cool down | Heaters + fan off | Low | Blocked while printing |
| `LOAD_FILAMENT` | Load | Heat + 90 mm extrude | Medium | Temperature gate, state gate, timeout |
| `PURGE_MORE` | Purge more | 30 mm extrude | Low | `can_extrude`, state gate |
| `UNLOAD_FILAMENT` | Unload | Heat + 80 mm retract | Medium | Temperature gate, state gate, timeout |
| `FILAMENT_DONE` | Done | Nozzle heater off (unless paused) | Low | — |
| `_SS_RUNOUT` | (sensor) | Records state, message | Low | Klipper already paused |
| `M600` | (slicer color change) | Calls Mainsail's `PAUSE` (retract + park) | Low | No heating or extrusion of its own. Ignored if already paused. Resume reheats via the UI or Mainsail's RESUME |

## Things to tune/verify on the real printer (Phase 3.5)
- `load_mm` (60) = gears-to-nozzle length on this extruder; `unload_mm` (80) clears the gears.
- `max_extrude_only_distance` ≥ 80 in the real config.
- TPU load speed (120 mm/min) on this extruder.

## Bench limits
The bench heaters are fake (Pi CPU temperature, ~40 °C), so on the bench we can test: the speed and flow macros, preheat/cool-down targets, every refusal path (cold, printing, unknown material), the timeout, and the remembered-material variable. The actual extrusion paths can only run on the real printer.
