---
name: printer-config
description: Safely change the StarStack S1's Klipper setup (config/s1/printer.cfg, macros/starstack_macros.cfg, moonraker.conf, the Orca start G-code, board firmware) and tune it (pressure advance, input shaper, speeds, currents, temperatures). Use when asked to edit printer.cfg, add or fix a macro, tune or commission the printer, change a speed preset, flash the board, or deploy config to the S1 or bench Pi.
---

# Changing the S1's printer config and macros

Klipper's own limits (`max_temp`, `min_extrude_temp`, thermal protection, endstops) stay the final
authority; nothing here may weaken them (PLAN section 3, test-checklist S5).

## Procedure
1. Read the related D-NNN entries in `docs/DECISIONS.md` and the matching section of
   `docs/macro-safety-review.md`. Check that the printer is idle before planning any restart.
2. Make the change on `dev` (debug experiments on `bench`, D-061). Keep values in config or `_SS`
   variables, not scattered through macro bodies.
3. Run `python tools/check_macros.py`. It parses and compiles every macro and rejects forbidden commands
   and names Klipper would misread.
4. Update `docs/macro-safety-review.md` for every new or changed macro, including the global checks table.
   It has to stay literally true.
5. Get the user's OK, then deploy (see [deploy-to-pi.md](deploy-to-pi.md)): back up on the Pi first, deploy
   only while idle, read Klipper's state and log afterwards.
6. Test on the printer with the user (heating and motion tests need their approval) and record a new Run
   section in `docs/test-checklist.md`.
7. Log it: a D-NNN row at the top of the Decisions table and a build/deploy log row.

Commissioning a printer from scratch, or after a board or wiring change: [commissioning.md](commissioning.md).

## Gotchas
- **Moonraker `trusted_clients` lists every private range**: `10.0.0.0/8`, `172.16.0.0/12`,
  `192.168.0.0/16`, `169.254.0.0/16`, `127.0.0.0/8`, `FE80::/10` (plus `::1/128`). Never one subnet: that
  locked the user out three times. Supersedes D-014's single `192.168.0.0/24` (D-102).
- **`config/s1/` is the old prototype**, not the production S1 (user, D-102). Its travel and speed limits
  are that machine's (Q-050). Production dimensions and specs: check the claude.ai project, don't assume.
- **TMC `run_current` is RMS, not peak** (user, D-102). Convert motor datasheet peak ratings before setting it.
- **Macro names with letters then a digit** (`_S1_PAUSE_FAN`) run as command `_S1`, so they silently never
  ran. Use names without digits; `check_macros.py` rejects them (D-089). Same for `rename_existing` targets.
- **Never block on heat in a macro** (M109, M190, TEMPERATURE_WAIT): while Klipper waits nothing else runs,
  not even Cancel. Heat, then poll from a `delayed_gcode` timer like `PRINT_START` (D-032, D-089).
- **The Orca start G-code is coupled to `PRINT_START`.** Orca adds its own M190/M109 unless the start G-code
  sets temperatures itself; keep `M140 S[...]` and `M104 S0` before `PRINT_START`
  (`config/s1/orca-start-gcode.txt`, D-089, Run 9). Changing PRINT_START's parameters means the user
  re-pastes the start G-code in Orca.
- **Pressure advance lives per filament in Orca.** The file's `SET_PRESSURE_ADVANCE` overrides printer.cfg
  (0.04 from the PETG profile vs 0.025 in the config, D-094). Tune it in the Orca filament profile.
- **The slicer owns acceleration.** Orca sends `SET_VELOCITY_LIMIT ACCEL=` thousands of times per print, so
  a speed factor (`M220`) never limits acceleration, and travel above `max_velocity` stays at the cap. Quiet
  modes need the wrappers from D-101.
- **A macro that "heats, then runs again" moves twice when the nozzle is already hot**: the touchscreen's
  first call already moved the filament. Heat-only calls take `HEAT=1` (D-097).
- **Prompts sent at the moment a print pauses vanish**: the touchscreen resets its pages on "paused". Send
  them from the next timer tick (D-090).
- **printer.cfg is copied to the Pi, never linked**: Klipper writes PID and mesh results into it
  (`config/README.md`). After `SAVE_CONFIG` on the Pi, copy the values back into the repo (D-084).
- **Board firmware goes through Katapult with the 16 KiB offset**; `make flash` doesn't work on this board
  (D-083, `config/README.md`). The update helper normally does this (D-087).
- **The bench config must never reach the printer**: its fake heaters sit on logic pins on purpose (D-027).
- **Pins shared with a driver's DIAG line float or read inverted** (bench v2 log, D-033 phantom runout).
- **`SET_KINEMATIC_POSITION` and `FORCE_MOVE`** are on the safety review's never list. Only the planned power
  loss recovery may use the first, for Z only, with a safety review section first (D-098).
- **Input shaper needs an accelerometer** the S1 doesn't have yet (B-17); the touchscreen page only reads results.
