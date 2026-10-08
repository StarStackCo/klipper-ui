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

## Run 5: Upstream KlipperScreen v0.4.7-196 (B-2), 2026-10-05 (bench v2.2, fork dev → starstack)

| Check | Result | Notes |
|---|---|---|
| Home idle: Print again + thumbnails | ✅ | After fixing a history refresh loop (thumbnails never landed) |
| Print / Controls / Settings pages | ✅ | |
| Console + keyboard | ✅ | |
| Load filament, nozzle adjust | ✅ | |
| Demo print: printing screen, speed, layer, thumbnail | ✅ | "Color change in –" fixed to "under 1 min" |
| Color-change pause → Change filament / Resume (reheat first) | ✅ | Bench heater can't reach 240°, so resume itself not completed (expected) |
| Cancel object | ✅ | Klipper `excluded_objects: [HANDLE_1]` |
| Cancel print (confirm) | ✅ | Heaters off, STOP back to gray |
| STOP → confirm → Printer stopped → Details → Restart | ✅ ×3 | Fixed: empty box, Details button, stuck "Starting printer" |
| SSH logout doesn't restart the screen | ✅ ×3 | Fixed (fork change #15) |
| Wi-Fi page opens | ✅ | Stock look (B-6) |
| KlipperScreen log | ✅ | No tracebacks |

## Run 6: Boot screen, faster boot, watchdog, Advanced pages, 2026-10-06 (bench v2.2, release klipper-ui PR #6 / fork PR #11)

Summary (details in DECISIONS.md D-067..D-080 and the build/deploy log):

| Check | Result | Notes |
|---|---|---|
| Boot: logo from power-up, no white/black gaps, bar reaches the end | ✅ | Boot to Home 32–35 s (was ~40 s) |
| "Touchscreen app didn't start" screen at boot and after a stopped app | ✅ | Shows the Mainsail address |
| App restart → back on Home | ✅ | |
| Pop-ups don't cover the left rail | ✅ | |
| Klipper, Moonraker, KlipperScreen, splash services up after reboot | ✅ | |

## Run 7: StarStack S1 full printer, 2026-10-07/08 (S1 config v1 → v1.1, Micro4 firmware v0.13.0-501)

Staged power-up, each stage approved by the user (D-081..D-085):

| Check | Result | Notes |
|---|---|---|
| Unplugged temperature sensors stop the printer | ✅ | "ADC out of range" (min_temp 0 fix) |
| Bed thermistor + heater | ✅ | 20.6 → 40 °C, holds; heater check quiet |
| X/Y/Z motors: right axis, right direction | ✅ | STEPPER_BUZZ + FORCE_MOVE (force move off again afterwards) |
| Sensorless homing X (195) and Y (206) | ✅ | Stops at the ends, no grinding |
| Hotend thermistor + heater, hotend and part fans | ✅ | 22 → 60 °C in ~14 s; fans spin (user) |
| Probe, Z homing, extrusion | ✅ | Tested by the user by hand |
| First full print (Benchy, slicer start G-code: G28, NOZZLE_CLEAN, mesh) | ✅ | 51 min, complete |
| PID re-tune nozzle 220 °C / bed 60 °C, SAVE_CONFIG | ✅ | Values in D-084 |
| Release on the S1: `_SS` macros show TPU 50 °C and 50/60/100 mm; services up; devtools off | ✅ | |
| Mainsail at http://starstack-s1.local | ✅ | D-085 |
| Touchscreen walk-through on the S1 | ⚠️ | Part 1 done (Run 8). Part 2 (heating, moving, printing from the screen) still to do |

## Run 8: S1 touchscreen walk-through, part 1 (no heating or moving), 2026-10-08 (fork dev 6717b3d2)

Driven with devtools (switched on for this run only) and screenshots in `design/klipperscreen/s1-*.png`, `s1-run/`.

| Check | Result | Notes |
|---|---|---|
| Home idle: newest file, Print again, loaded filament, Preheat / Load / Cool | ✅ | |
| Top bar: nozzle and bed temperatures | ❌ → ✅ | Missing since the v0.4.7 merge; fixed (fork #48, D-086) |
| Print a file (11 pages, thumbnails, sort) | ✅ | |
| Controls (heaters, fan, filament, move) | ✅ | |
| Settings + About (name `starstack-s1`, Ethernet IP, Klipper version) | ✅ | |
| Advanced pages open: Screen, Wi-Fi, Shut down/reboot, Updates, Fans, Move, Extrude (blocked when cold), Bed mesh, Input shaper, Console, Adjust | ✅ | No errors in the KlipperScreen log |
| Part 2: load/unload from the screen, start a print, pause, resume, cancel, STOP | ⏳ | Needs the user at the printer |

## Run 9: start of print and cancel (PRINT_START, D-089), 2026-10-08 (klipper-ui dev b6dd199, fork dev 6ceb71e3)

Found by the user: canceling while the bed heated kept heating and showed "printing" until the bed
reached 80 °C; a red `Unknown command "_S1"` on cancel. Tests 1–3 run by Claude with a 4-line test
file (`ss_bench_start_cancel.gcode`: `PRINT_START BED=60 EXTRUDER=150`), bed step only, no motion.

| Check | Result | Notes |
|---|---|---|
| S1 config v1.2 loads, no warnings; `PRINT_START` present | ✅ | Backup `printer.cfg.pre-d089` on the Pi |
| Start → file pauses in the background, bed heating, "Heating bed 31/60°C" | ✅ | |
| RESUME while getting ready is refused | ✅ | Mainsail refuses (cold nozzle); `_SS_RESUME_GUARD` refuses when hot |
| Cancel while the bed heats | ✅ | 0.34 s to canceled, heaters off; no `_S1` error |
| Heat time limit (set to 6 s for the test) | ✅ | Canceled with "the bed didn't reach 60°C…", heaters off, status cleared; limit back to 600 s |
| Touchscreen while getting ready | ✅ | "Heating bed 36 / 60°" + heat bar, "Getting ready" (grayed), no %/time left; back to Home after cancel |
| Full start with the new Orca start G-code: bed → nozzle → home → clean → cool to 150 → mesh → park → heat → purge → print | ✅ | Benchy PETG 80/245: bed 4 min, nozzle 1 min, home + clean, cool 1 min, mesh 1 min, park Z15, heat 46 s; ~8 min to the purge line; resumed in place. Mesh: right side ~1.6 mm lower than left (compensated; tram later) |
| Orca adds no M190/M109 of its own before `PRINT_START` | ✅ | `M140 S80`, `M104 S0`, `PRINT_START BED=80 EXTRUDER=245`; no M190/M109 anywhere in the file |
| Cancel while getting ready (touchscreen) | ✅ | Twice during bed heat: canceled in 1–3 s, heaters off. Still homed from the previous print → cancel lifted 50 mm; not homed → no move |
| Pause/resume: part fan off and back; cancel: nozzle lifts | ✅ | Pause: park + fan 39 % → 0; resume: fan back to 39 %; cancel while printing: heaters off at once, lift 10 + 40 mm. No `_S1` error. User: "everything works as intended" |
| Old file (M190/M109): Cancel on the touchscreen → "Canceling…", then emergency stop + restart after 3 s | ✅ | `Main(27)_PETG_4h44m`: backstop fired 16:01:49, firmware restart 16:01:51, ready again, heaters off |

## Run 10: filament check before printing (D-090), 2026-10-08 (klipper-ui dev 546633d, fork dev a6a084d8)

| Check | Result | Notes |
|---|---|---|
| PRINT_START with nothing loaded: waits, asks on the touchscreen and in Mainsail | ❌ → ✅ | First the question vanished: the touchscreen resets its pages when the print turns "paused". Now asked 1 s later from the timer. Buttons PLA / PETG / TPU in one row |
| Answer PETG in the question | ✅ | Recorded, question closed, moved on to heating the bed (canceled before any motion) |
| No answer within the limit (set to 3 s for the test) | ✅ | Canceled with a message, heaters off, question closed; limit back to 600 s |
| Touchscreen Print, nothing loaded → "No filament loaded" → It's loaded → PETG → "Is the bed clear?" | ✅ | User; Not yet, nothing printed |
| Touchscreen Print, PLA loaded, PETG file → "Different filament loaded" | ✅ | User; Go back. PETG recorded again afterwards |
| Load filament from the question → back to Print | ⏳ | Not tried yet (same load flow as before + return to Print) |

## Run 11: kernel/boot packages held (D-092 part 4), 2026-10-08 (klipper-ui dev 0812b02)

| Check | Result | Notes |
|---|---|---|
| `install.sh --dry-run` lists the packages to hold | ✅ | 8: linux-image/dtb/u-boot (BTT vendor), armbian-bsp-cli, armbian-firmware, armbian-config, initramfs-tools(-core) |
| User ran `install.sh --printer=s1`: packages held, list saved for uninstall | ✅ | `apt-mark showhold` + `/var/lib/starstack/held-packages` |
| `apt-get -s upgrade` keeps them back | ✅ | 252 others would install |
| Moonraker (PackageKit) "system" list skips them | ✅ | 256 → 252 after a refresh; none of the held packages listed |

## Run 12: update health check, automatic undo, Undo button (D-092 part 1), 2026-10-08 (klipper-ui dev c45d69e..85e959e, fork dev f1ad0ca5)

| Check | Result | Notes |
|---|---|---|
| User re-ran `install.sh --printer=s1`: helper runs with `SupplementaryGroups=moonraker-admin` | ✅ | |
| First run records the last known good (5 repos + Mainsail v2.19.0 + 3 config files) | ✅ | 16:40:52 |
| Good update (klipper-ui forward one commit) → checked, new good, "Undo last update" offered | ✅ | Checked within seconds |
| Bad update (throwaway local commit breaking the macros, Klipper restarted → error) | ✅ | Noticed 16:42:10; after 5 min put klipper-ui back, restarted Moonraker and Klipper itself (16:47:13–20); Klipper ready, repo level with GitHub again |
| Undo message on the console | ❌ → fix | Sent while Klipper was down, so only the Updates page showed it. Fixed in 85e959e (repeats it once Klipper is ready); needs the next `install.sh` run to reach the S1 |
| "Undo last update" on the touchscreen (user) | ✅ | 23 s: back one version, Moonraker + Klipper restarted, Klipper ready; Undo row gone afterwards (one step) |

