# Safety and Regression Checklist

Run on **every increment** before merging. Copy the results table into a new "Run" section at the bottom and fill it in.
Result key: ✅ pass · ❌ fail · ⚠️ pass with a note · ➖ not testable in this environment (say where it gets tested)

## Safety, must always pass

| ID | Check | How |
|---|---|---|
| S1 | Emergency Stop reachable from every screen on both UIs, at most 1 tap/click away | Visit every screen and check |
| S2 | Cancel print, firmware restart, shutdown and reboot ask for confirmation | Trigger each one and check a confirmation dialog appears |
| S3 | Axis moves and homing disabled/locked while printing | Start a print, try moving the axes |
| S4 | Heater inputs can't exceed configured `max_temp`. The UI shows Klipper's real reported values | Try to set above max. Compare the UI with `/printer/objects/query` |
| S5 | New/changed macros don't alter or bypass `max_temp`, `min_extrude_temp`, `verify_heater`/thermal runaway, or endstops | Review macro diff + `grep` |
| S6 | Extrude/retract blocked or warned when the hotend is cold | Try extruding cold |
| S7 | Error/shutdown states obvious (colour **and** text) | Trigger a safe shutdown (e.g. `M112` on the bench) and check both UIs |
| S8 | No secrets (passwords, API keys, tokens) committed | `git grep -iE "password|api_key|token|secret"` |

## Functional, nothing broken

| ID | Check | How |
|---|---|---|
| F1 | Klipper starts with no config errors (state `ready`) | `/printer/info` |
| F2 | Moonraker running, no warnings or failed components | `/server/info` |
| F3 | Mainsail loads from the PC | Browser |
| F4 | Mainsail mobile layout usable | Browser, mobile viewport |
| F5 | KlipperScreen connected, no error screen | `scripts/ks-screenshot.sh` |
| F6 | Live data updates (temps, position, progress) on both UIs | Watch values change |
| F7 | Home, jog, preheat, cooldown, fan, load/unload filament | Hardware |
| F8 | Upload, start, pause, resume, cancel a print | Hardware |
| F9 | Live tuning: speed, flow, Z babystep | Hardware, during a print |
| F10 | Bed mesh and Z offset workflows (PZ probe) | Hardware |
| F11 | Rollback restores the previous state | Run rollback, then F1–F5 |
| F12 | No new under-voltage events on the Pi | `dmesg \| grep -i volt` |

---

## Run 0: Baseline, 2026-10-04 (bench: BTT Pi + TFT35 SPI + FLY Micro4, nothing wired, bench printer.cfg v1, stock Mainsail v2.17.0 / KlipperScreen v0.4.6)

Screenshots: `design/baseline/`

| ID | Result | Notes |
|---|---|---|
| S1 | ⚠️ | **Mainsail:** E-stop in the top bar on desktop (text) and mobile (icon) ✅. **KlipperScreen:** no E-stop visible on the idle home screen (`klipperscreen-home.png`). New design must fix this |
| S2 | ➖ | Not exercised. Will test after themes are applied (bench, no print needed for restart/shutdown dialogs) |
| S3 | ➖ | Needs printer + print → Phase 3.5 |
| S4 | ➖ | No heaters on the bench → Phase 3.5 |
| S5 | ✅ | No macros added yet. Bench config includes only `mainsail.cfg` |
| S6 | ➖ | No extruder on the bench → Phase 3.5 |
| S7 | ➖ | Not exercised yet |
| S8 | ✅ | Repo contains no secrets. Backups and SSH logs are git-ignored |
| F1 | ✅ | `state: ready` |
| F2 | ✅ | No warnings, no failed components (crowsnest service failed: no camera, unrelated) |
| F3 | ✅ | HTTP 200 and user confirmed |
| F4 | ✅ | Renders. Usable but dense |
| F5 | ✅ | User confirmed. Screenshot captured remotely |
| F6 | ⚠️ | KlipperScreen shows Pi + MCU temps live. **Mainsail Temperatures panel is empty** although the sensors exist. MCU temp reads wrong (-17.9 to -22.9 °C, Q-018) |
| F7–F10 | ➖ | Need hardware → Phase 3.5 |
| F11 | ⚠️ | On-Pi undo copies exist (`*.pre-klipper-ui`, `printer.cfg.old-machine`). Rollback script not written yet |
| F12 | ✅ | 0 under-voltage events |

## Run 1: Mainsail theme v1 + settings, 2026-10-04 (bench v2)

Screenshots: `design/mainsail/theme-v1-*`

| ID | Result | Notes |
|---|---|---|
| S1 | ✅ Mainsail | E-stop solid red in the topbar on desktop (text) and mobile (icon). TFT not changed yet |
| S2 | ⚠️ | **E-stop now asks "Are you sure?"** ✅ (dismissed with NO/Escape, Klipper stayed `ready`). Cancel-print confirmation set (`confirmOnCancelJob`), needs a print to test → bench print test later |
| S5 | ✅ | No macros changed |
| S8 | ✅ | No secrets in the theme or settings |
| F1 | ✅ | `ready` (also after the power loss and reboot; config hashes match the repo) |
| F3 | ✅ | Loads with the theme. Logo, font and colours applied |
| F4 | ✅ | Mobile stacks in one column after a reload. Resizing without reloading shows a squeezed layout (Mainsail behaviour, not the theme) |
| F6 | ✅ | Temperatures panel now shows Extruder + Heater Bed live (bench v2). Q-020 resolved |
| F11 | ✅ ready | `deploy-mainsail-theme.sh --rollback` and `mainsail-settings.sh --rollback` exist (not exercised) |
| F12 | ⚠️ | No under-voltage logged, but the Pi **lost power** once (hard reboot, PC USB power). Config intact |

## Run 2: Macros v1 + bench v2.2, 2026-10-04 (user present, heating/motion tests approved)

Automated: `scripts/bench_test_macros.py` (run on the Pi) → **34/34 PASS** (run 3; full log in local `logs/bench-test-run3.txt`).

| ID | Result | Notes |
|---|---|---|
| S4 | ✅ (bench) | Preheat targets exact (210/60, 225/40). Unknown material → no heat |
| S5 | ✅ | Static scan: no safety-limit commands in macros. See `docs/macro-safety-review.md` |
| S6 | ✅ (bench) | Load/Purge/Unload refuse when cold (heat + ask to rerun). Klipper min_extrude_temp underneath |
| S3-macros | ✅ | During a real (bench) print: preheat, cool-down, load, unload, purge all **refused**. Speed preset allowed |
| Paused flow | ✅ | Load allowed while paused. FILAMENT_DONE keeps the heater on for resume |
| Timeout | ✅ | Abandoned filament heater turns off (tested with 3 s) |
| Cancel | ✅ | CANCEL_PRINT → state cancelled, heaters off |
| Memory | ✅ | `loaded_material` saved/used/reset via save_variables |
| Flow limits | ✅ | 200 → 120 %, 10 → 40 % with warnings |
| UI → macro | ✅ | Clicking SPEED SILENT in Mainsail (localhost) → speed_factor 0.5, reset to 1.0 |
| Z-offset hidden | ✅ | `view.toolhead.showZOffset=false` applied. Toolhead panel goes from jog to Speed factor |

**Finding:** in runs 1–2 the **runout sensor triggered falsely** on the bench (pin floating, shared with driver DIAG), causing a phantom PAUSE. Fixed for the bench by disabling the sensor at startup (bench v2.2). The real printer must verify its sensor reads stable (Phase 3.5).
**Note:** Mainsail's own PAUSE/CANCEL macros log `"extruder" not hot enough` on the bench (they retract; fake nozzle is cold). Expected.

## Run 3: StarStack touchscreen v1, 2026-10-05 (bench v2.2, macros v1 + M600)

Driven remotely with `scripts/ks-tap.sh` (bench devtools) and `scripts/ks-screenshot.sh`. Screenshots: `design/klipperscreen/` (v1-*, v2-*, final-tour.png). Demo print: `scripts/make_bench_print.py` (thumbnail, 4 objects, 40 layers, M73, M600 at layers 12/28).

| ID | Result | Notes |
|---|---|---|
| S1 | ✅ | STOP in the rail on every page, pop-up and the stopped screen. **Red when active** (printing, heater on, busy), **gray when idle**, always tappable |
| S1-guard | ✅ (fixed) | A macro prompt grew the window to 478 px and pushed STOP off-screen. Fixed by the content guard (window stays 320 px, page scrolls) |
| S2 | ✅ | Confirmations: STOP, Cancel print, Cancel part, Restart printer, Advanced mode, Bed clear. All appear in-page with the rail visible |
| S3 | ✅ | Controls: filament + move locked (dashed) while printing. Shut down locked while printing |
| S7 | ✅ | E-stop → "Printer stopped · Emergency stop was pressed" (red), rail disabled, Restart printer (confirm) → back to Home, Klipper ready |
| F5 | ✅ | KlipperScreen active after every deploy. No tracebacks from StarStack code |
| F6 | ✅ | Live temps, progress (G-code-body based, matches layers), time left |
| Home | ✅ | Idle: 3 recent prints with real thumbnails, preheat. Printing: job card, speed chips, tiles. Done card |
| Print | ✅ | 6 per page, sort cycle, pager, disabled while printing |
| Cancel object | ✅ | Bed map (180 mm), list, confirm, last-part → cancel-print guard |
| Adjust | ✅ | Nozzle +10 applied (target 250) |
| Color change | ✅ | 2 changes found. Line alternates "Color change in 1 min" / "2 min left". M600 → pause → "Color change" + Change filament |
| Reheat-resume | ✅ (bench) | Paused with cold nozzle → Resume shows "Reheating to 240°, then resuming". Completion only on the real printer (fake heater) |
| Filament | ✅ | Pick → heating bar (43°/240°) → (hot steps need the real printer). Visibility bug fixed |
| Prompts | ✅ | Macro prompts shown in-page, OK works, rail visible |

**Bench-only noise:** Mainsail's PAUSE/RESUME print "extruder not hot enough" banners (fake cold nozzle).

## Run 4: On-screen keyboard (B-1), 2026-10-05 (bench, fork dev → starstack v0.4.6-46)

| Check | Result | Notes |
|---|---|---|
| Keys ≥ 44 px tall | ✅ | 44 px, 4 rows all visible (Console) |
| Edge margins | ✅ | 16 px bottom, 16 px right (measured from screenshot) |
| STOP rail visible while typing | ✅ | Keyboard lives inside the page area |
| Title bar restored on close | ✅ | Closing via the rail |
| Style matches UI | ✅ | Dark flat keys, 8 px corners, blue when pressed. Screenshot `design/klipperscreen/kbd-console.png` |
| Wi-Fi password entry | ➖ | Same keyboard code path. Not exercised on the bench, to avoid dropping the Pi's Wi-Fi |
| Clean shutdown before unplug | ✅ | Previous boot ended with a normal power-off. All repos fsck clean |
