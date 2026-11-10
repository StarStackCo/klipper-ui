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
| v0.3.1 installed (user ran `install.sh --printer=s1`); klipper-ui stepped back to v0.3.0 and forward to v0.3.1, Klipper restarted each time | ✅ | "healthy, waiting a minute", then checked 62 s later both times; S1 left on v0.3.1, clean, Klipper ready |

## Run 13: dev batch on the S1 (D-094..D-097, D-101), 2026-10-31 (klipper-ui dev 7413669, fork dev 9f3ed0f3)

| Check | Result | Notes |
|---|---|---|
| Klipper loads the v1.2 macros | ❌ → ✅ | `M204` renamed to `_SS_ACCEL_BASE` stopped Klipper ("rename of different types"); now `M204.1`, and `check_macros.py` catches it |
| Silent caps (no motion): SPEED_SILENT → 100 mm/s, accel 800, corners 3; file's ACCEL=2000 and M204 S1500 capped to 800; ACCEL=500 kept; SPEED_NORMAL → 200 / 2000 / 6 | ✅ | |
| Touchscreen: quick taps register, no ghost opens (D-094) | ✅ | User |
| Pause double tap → Pausing…, stays paused; Resume double tap → Resuming… (D-095) | ✅ | User |
| PETG start from a cold bed: soak countdown, Skip soak, mesh after the soak; warm-bed reprint skips it (D-096) | ✅ | User: heat soak worked. A restart right after a canceled start skipped it (bed within 10 °C): kept as designed (user) |
| Change filament on pause, load, unload: each move once, 1 mm retract, 40 mm purge, clean tip (D-097) | ✅ | User: change filament worked |
| Silent on a real print: travel and gyroid quieter; Normal speeds back up (D-101) | ✅ | User: "Silent works very well". Draft = 1.5× but infill/travel stay at the 200 mm/s limit (→ 400, D-103) |
| Speed limit 400 mm/s live, Draft, accel 2000: 45 s of live speed | ✅ | Peak 205 mm/s, 99 % under 183: acceleration, not the limit, sets the speed on this part |
| Accel 4000 held for 5 min (2000 sections bumped, outer walls left at 500), Draft, 400 mm/s | ✅ | Peak 300 mm/s (Draft infill 200 × 1.5), 99 % under 260, 18 % of the time above 100 mm/s (was 8 %). No layer shifts (user). X squeaks on long moves: check belt tracking and rails |
| printer.cfg v1.3 installed: limit 400 mm/s | ✅ | Backup `printer.cfg.pre-d103` |
| Silent part fan (D-103): any fan-on → 30 %; Normal restores the last asked speed | ✅ | M106 S255 → 30 %, S128 → 30 %, Normal → 50 %, M107 → off |
| Default speed (D-104): Settings row, restored after a canceled/finished print | ✅ | User: Silent as default, canceled print came back to Silent |

## Run 14: upstream merge, error handling, file checks (D-105, D-106), 2026-11-02 (klipper-ui dev 50cfa9e, fork bench 8f-series on 34610cea upstream)

Run by Claude through Moonraker and the bench devtools (switched on for this run), with screenshots.

| Check | Result | Notes |
|---|---|---|
| Pages after the upstream merge: Home, Print, Controls, Settings 1–5, Screen & language, Default speed, Installed nozzle, Updates, About, Wi-Fi | ✅ | No log errors. Top-bar page title on Settings sub-pages ("Screen", "Updates", "About"): not new, Settings always passed the title (opened directly: no title) |
| Settings jumped back to page 1 after every sub-page | ❌ → ✅ | Now returns to the page it was opened from; from the rail still page 1 |
| Updates: "1 updates" | ❌ → ✅ | "1 update" |
| File for a 0.6 mm nozzle (0.4 installed) | ✅ | Canceled at once, both heaters stayed off, red error page, console line |
| File for another printer ("Bambu Lab X1C") | ✅ | Same |
| File with a part outside the bed | ✅ | Same; Klipper shows part names in capitals (FAR_PART) |
| Error page "Klipper:" line | ❌ → ✅ | Showed the previous StarStack error; now blank when Klipper reported nothing |
| Error page "Print again" on refused files | ❌ → ✅ | Hidden for outside-the-bed, nozzle and printer refusals |
| PLA file, PETG loaded | ✅ | Waits before heating; question on the touchscreen and in Mainsail; Home: "This file is for PLA" + Change filament |
| Print anyway (Mainsail answer, then the new Home button) | ✅ | Bed starts heating, answer used up; Cancel: heaters off |
| Retry: Z homing fails once (`start_fail_test=home_z_once`) | ❌ → ✅ | First run recovered but logged "Macro _SS_START_RUN called recursively" (homing called the clean step inside the same macro); fixed (404757b): the tick starts the next step. Rerun: fail → "trying again (1/2)" → re-home → clean → cool, no stray errors |
| Retry: Z homing fails every time (`start_fail_test=home_z`) | ✅ | 1/2, 2/2, then canceled by itself (~30 s), heaters off, red error page with Klipper's line, Print again shown |
| Clean-up | ✅ | Test switch off, error cleared, devtools removed, touchscreen restarted |
| Real start (Benchy, PETG, cold bed): soak, mesh 1.60 mm → uneven-bed warning | ⚠️ → fixed | Warning sent as a red error pop-up; the print was canceled from the touchscreen 15 s later (looked like a failure). Now a plain console message + "Bed uneven 1.60 mm" in the Home status line + amber card after the print |
| Retry: nozzle clean fails once (`clean_once`) | ✅ | Clean failed → trying again (1/2) → re-home → clean → cool |
| Retry: bed mesh fails once (`mesh_once`) | ✅ | Mesh failed → re-home → straight back to the mesh (no clean) → mesh done → heating for the print |

## Run 15: dev update, unload tip forming and extruder load test (D-117, D-118, D-124, D-125), 2026-11-09 (klipper-ui dev f554fab, fork dev 79d217be)

After the Main Body(2) PLA print. Load tests run by Claude with `tools/sg_test.py` (data in `docs/data/sg_test.json`); tip and touchscreen checks by the user.

| Check | Result | Notes |
|---|---|---|
| S1 on dev: Klipper ready, touchscreen up, no log errors | ✅ | Klipper side by the other session (printer.cfg.pre-d118); touchscreen bench → dev |
| `sg_test.py` runs | ❌ → ✅ | Status query URL-encoded the `&`, so Moonraker returned neither object; fixed before anything was sent |
| Load test, PLA loaded, 210 °C, 2/5/8/12/16/20 mm³/s | ✅ | SG_RESULT avg 16 / 46 / 69 / 88 / 107 / 123. Reads in steps of 32; rises with speed |
| Load test, PLA held back by hand (light drag, kept feeding) | ✅ | 16 / 45 / 65 / 81 / 106 / 125: same as loaded within noise |
| Load test, no filament | ✅ | 16 / 48 / 70 / 94 / 124 / 152: differs from loaded only above 12 mm³/s, by about one step |
| Klipper restart undoes the test's driver settings | ✅ | TPWMTHRS back to 0xfffff, TCOOLTHRS 0. GCONF shows StealthChop on at standstill: `stealthchop_threshold: 0` in Klipper means SpreadCycle whenever the motor moves |
| PLA unload tip (D-125 starting values) | ✅ | User: "a lot better, point looks good" |
| Print confirmation (D-124): "Print this file?" | ❌ → D-126 | User: it should say the file's name |
| Home Change filament | ❌ → D-126 | User: it should start the unload straight away |
| D-126 Print question: "Print Main Body(2)?" with material and time (fork dev 2e77b4a5) | ✅ | User |
| D-126 Home Change filament unloads at once, then asks for the new one | ✅ | User; log: UNLOAD 11:15:20 right after the tap, then LOAD PLA 11:15:52 |
| Walk-away load of PLA (Grab) | ✅ | User; loaded and purged, heater off |

## Run 16: release check for v0.5.0 → next (D-107..D-127), 2026-11-09 (klipper-ui dev, fork dev 2e77b4a5)

Run by Claude from the S1's history and logs; covers what the week of real printing exercised. Items not exercised are named.

| Check | Result | Notes |
|---|---|---|
| Prints since v0.5.0 (2026-11-02 19:00) | ✅ | 42 jobs: 29 completed, 10 canceled, 3 shutdowns; 74.3 print hours |
| Shutdowns explained | ✅ | 11-05 Saber PETG: "Timer too close" from the stall log (D-115, logging removed D-118); 64 lines in that day's log, none since. 11-08 Main Body ×2: cancel-while-heating backstop (D-089), now shown as "Print canceled" (D-116) |
| Ghost taps (D-112): touches under 45 ms passed on since the 11-05 fix | ✅ | 0 in 4 days (292 passed, 190 ignored). The two before the fix (23 and 24 ms, 11-05 00:26 and 12:37) opened the adjust page; the 11-06 opening followed a 72 ms press |
| Job queue (D-111) | ✅ | Deploy log 2026-11-03: idle and printing tests on the S1, user checked reorder and remove |
| Clock and job line (D-114, built part) | ✅ / not exercised | 12-hour clock in today's screenshots; finish time seen in real prints (user). "Don't show again" on a warning card not exercised |
| Filament flow (D-116, D-117, D-125, D-126) | ✅ | Run 15: walk-away load, one-tap Change filament, PLA tip. Prime and Purge more not exercised this week. PETG and TPU tips untested (user: later) |
| Klipper ready, no "Unknown command" or "Timer too close" since today's restart | ✅ | |
| Update Manager | ✅ | Klipper v0.13.0-501, Moonraker v0.10.0-2, Mainsail v2.19.0, mainsail-config v1.2.1-1, KlipperScreen and klipper-ui: all valid, clean, no warnings; 257 OS packages pending |
| Update helper changes (D-118) | not exercised | Root-installed: reach the S1 only when the user runs `install.sh` with sudo |

## Run 17: cold homing heats first (D-131, B-19), 2026-11-09 (klipper-ui dev after a5e8118, S1)

Run by Claude through Moonraker (same `G28` / `BED_MESH_CALIBRATE` the touchscreen and Mainsail send), user approved heating and motion.

| Check | Result | Notes |
|---|---|---|
| Home all from cold (24 °C) | ✅ | "Heating nozzle to 150°C to probe", 24 → 147 °C in about 32 s, Z homed, target back to 0; 52 s in all (first version) |
| Bed mesh, nozzle at 135 °C and heating (first version, waited for 145 °C only) | ❌ | 5 retries at X10 Y10: first sample 1.94 mm, each next one about 2.5 mm higher (probe fires in mid-air after the 3 mm retract); nozzle left at 150 °C, as designed after a failure |
| Bed mesh, nozzle steady at 150 °C for minutes | ✅ | First try, no retries, 60 s. Mesh 1.94 front left to -1.00 right: 2.9 mm, near D-105's 3 mm stop. Target 150 left as it was |
| Home + bed mesh from 99.5 °C, second version (148 to 152 °C, 15 s hold) | ❌ | Homing ✅; mesh started at a steady 150 °C and still failed: 5 retries, same pattern (1.98, then 4.3 to 13.8 mm). Test meant to start under 40 °C; the cool-down check let 99.5 °C through |
| Probe retries in earlier logs | info | 11-06: 0 retries in 10 meshes; 11-07: 0 in 6; 11-08: 17 retries, 2 failed; 11-09 before this run: 9 retries. Probe config unchanged since 10-07 |
| `PROBE_ACCURACY SAMPLES=10` at the homing point X133 Y185, nozzle steady 150 °C, `LIFT_SPEED` 10 / 8 / 5 / 3 | ✅ | 40 of 40 clean, no mid-air triggers. Range 0.019 / 0.007 / 0.003 / 0.011 mm, std dev 0.006 / 0.002 / 0.001 / 0.003 mm. Lift speed isn't the cause; every failure (today and 11-09's retries) was on the left edge, X10 Y10 and X10 Y170. Nozzle and mount not checked by hand yet |
| `PROBE_ACCURACY SAMPLES=10` on the left edge, nozzle steady 150 °C, travel at Z 10 | ❌ | X10 Y10 lift 10: 10 of 10 good, -0.075 mm (range 0.006). X10 Y10 lift 5: 6 of 10 false triggers (2.5 to 11.9 mm). X10 Y170 lift 10: 4 of 10 false (2.3 to 4.9 mm), real -0.27 mm. False triggers are random, not tied to lift speed |
| The "passing" mesh above | ❌ wrong | It read +1.94 mm at X10 Y10 three times; the real contact there is -0.07 mm. The mesh's 2.9 mm tilt is false triggers, not the bed. Meshes since about 11-08 (prints included) may be wrong the same way; don't tram from them |
| **After the user gave the toolhead cable more slack** (it was tight with Z down and the head far left) | | |
| Cold home + mesh from 37 °C (the touchscreen's `G28` then `BED_MESH_CALIBRATE`) | ✅ / ❌ | Homing ✅ (heated, settled, homed); mesh failed, 5 retries; 136 s. Nozzle left at 150 °C after the failure, as designed |
| `PROBE_ACCURACY` 10 samples, 150 °C steady, lift 10 / 5 mm/s | ❌ left edge | X133 Y185: 0 / 0 false (range 0.008 / 0.006, mean 0.00). X10 Y10: 4 / 2 false (2.27 to 9.31), good samples -0.06. X10 Y170: 4 / 1 false (2.35 to 12.11), good samples -0.25. Slack didn't fix it; false triggers mostly at 2.4 to 2.5 mm, about 0.4 mm into the descent after the 3 mm retract (B-23) |
| Second mesh, 150 °C steady | ❌ | 5 retries, failed |
| `PROBE_ACCURACY` 10 samples, lift 10, by **descent speed** (`PROBE_SPEED`), 150 °C steady | 5 mm/s ✅ | X10 Y10 / X10 Y170 false triggers: 20 mm/s (config now) 3 / 2; 10 mm/s 9 / 9 (every sample, Z resonance band, D-109); **5 mm/s 0 / 0 (range 0.002 / 0.005)**; 2.5 mm/s 0 at Y10, then "No trigger on probe after full movement" at Y170 (too slow for the piezo). At the homing point 2.5 mm/s triggered 0.8 mm into the bed, and the next set read -0.61 mm instead of 0, so Z likely skipped: re-home before using the printer. Points after that failure are not counted |
| **D-134 deployed (`[probe] speed: 5`)**: cold home + mesh from 39 °C | ✅ | 144 s, 0 retries, nozzle target back to 0. Mesh rows (Y10, Y90, Y170 × X10, X90, X170): -0.644 -0.200 0.020 / -0.807 -0.232 0.127 / -0.853 -0.174 0.162, range 1.01 mm. **B-19 done** |
| Hot mesh, 150 °C steady | ✅ | 73 s, 0 retries, every point within 0.03 mm of the cold mesh |
| `PROBE_ACCURACY` 10 samples at 5 mm/s | ✅ | X133 Y185: 0 false, range 0.030, mean 0.018. X10 Y10: 0 false, range 0.037, mean -0.630. X10 Y170: 0 false, range 0.003, mean -0.842 |
| Left edge reads lower at 5 mm/s than at 20 | ✅ resolved | X10 Y10 -0.63 at 5 mm/s vs -0.06 at 20 mm/s; settled by the paper test below |
| **Paper test** (user), nozzle cold (44 °C), mesh cleared, homed at 150 °C | ✅ | Homing point X133 Y185: free at Z 0.100, drag at 0.075. X10 Y10: free at -0.50, drag at -0.55. So X10 Y10 sits 0.600 to 0.625 mm below the homing point: the 5 mm/s probe (-0.63) is right, 20 mm/s (-0.06) was wrong. The D-134 mesh is trustworthy: bed about 1 mm out of level, left side low (X10 -0.64 to -0.85, X170 +0.02 to +0.16) |
| Mainsail's Home All button, nozzle cold (24.8 °C), clicked in the browser pane | ✅ | "Nozzle to 150°C to probe", 24.8 → 151.5 °C, 15 s hold, Z homed, target back to 0 after about 60 s; no "No trigger" in klippy.log |
| Idle home from a 210 °C preheat | ✅ | Cooled to 150 °C in 62 s, held, homed, target back to 210 °C; 77 s; no "No trigger" |
| Real print `Mesh test squares PLA` (Overture PLA, five 30 mm squares at the corners and middle, 2 layers), 2026-11-09 22:29 | ✅ | Every `PRINT_START` stage ran (bed, nozzle 185, home, clean, cool 150, mesh 74 s, final 205); completed in 14 min; 0 probe retries. **User: all five squares even** (corners and middle), so the 5 mm/s mesh gives an even first layer |
| Next print `Main Body(2)_PLA_7h11m` 22:45 | ❌ | `PRINT_START` Z homing: "No trigger on stepper_z after full movement" 3 times (nozzle hot, homing at `homing_speed` 20 mm/s), canceled by the D-105 retries after 2 min (B-24). Restarted 23:21: homed, mesh 0 retries, printing. Its mesh (Y10/Y90/Y170 rows): -0.222 0.191 0.419 / -0.416 0.190 0.518 / -0.506 0.236 0.587, same X10→X170 rise as the D-134 meshes (0.64 / 0.93 / 1.09 vs 0.66 / 0.93 / 1.02) |
| Since the D-134 restart (21:26) | ✅ / ❌ | 0 mesh retries in every mesh; 3 "No trigger" lines, all from the 22:45 homing |
| Not exercised | | `PROBE_CALIBRATE` |

## Run 18: first power-up setup on the S1 (D-137), 2026-11-10 (fork first-power-up 3f9ed6fe, S1)

Run by the user on the touchscreen (Settings > Setup and tour), three passes; fixes between them were installed with `ks-update.sh --branch first-power-up`.

| Check | Result | Notes |
|---|---|---|
| Welcome: Start only | ✅ | Skip setup removed (user) |
| Time zone: tap sets the Pi's zone, chosen zone shows | ❌ → ✅ | Taps worked from the start (Pi went Denver, then New_York) but the outline never drew, then the page read a stale `/etc/timezone` (Europe/London). Now solid blue with a check, read from `/etc/localtime`. Other zone / 12-hour / 24-hour row removed (it made the page scroll), buttons 50 px |
| Time zone without a password | ✅ | polkit rule (installed by hand, user typed sudo); `timedatectl --no-ask-password set-timezone` as biqu |
| Wi-Fi: Done returns to the setup | ✅ | |
| Rail during setup: STOP only, then icons shown but not tappable from the tour, tour highlights each | ❌ → ✅ | First version: nav icons vanished on every page (no_show_all hid the image); fixed |
| Nozzle tap (cold PZ) registers | ❌ → ✅ | PZ LED lit but nothing registered: the endstop is `stepper_z`, code read `z`. One endstop query takes ~300 ms on the S1, polled back to back |
| "The probe works" OK page, then heating; "Next: homing" OK page, then G28 | ✅ | Added at the user's request |
| Heaters, part fan question, homing, "Self-tests complete" | ✅ | |
| Tour, filament, first print | ✅ | First print is `3DBenchy Overture PLA.gcode` (re-sliced, PRINT_START). The first try used the old `3DBenchy_PLA_1h6m.gcode` (blocking `M190`): Cancel queued behind it and the backstop e-stopped (B-25); the setup now offers only PRINT_START files |
| Cancel on the new first print | ✅ | Cancels cleanly, no restart (user: "everything works") |

## Run 19: setup clock, hot nozzle and tap page layout (D-137), 2026-11-10 (fork first-power-up 68d8367a, S1)

Run by Claude with the bench dev tool (`~/.starstack_dev`, removed afterwards), after the user reported: zone tap didn't change the clock, tap page text pushed off the side, a hot nozzle still asked for a tap.

| Check | Result | Notes |
|---|---|---|
| Zone page fits, chosen zone marked | ✅ | Screenshot: Eastern solid blue with a check, 6 buttons and Back / Skip / Next on screen |
| Clock follows a zone change at once | ✅ | Central picked: top-right clock 02:00 PM → 01:01 PM straight away (KlipperScreen only redrew on a new minute). Set back to Eastern (`timedatectl`: America/New_York) |
| Hot nozzle: wait page | ✅ | Nozzle 51°C: "Wait for the nozzle to cool", live temperature, no tap request, No reaction grayed; Stop / Skip / No reaction all on screen |
| Switches to the tap by itself | ✅ | At 44°C: "Tap the nozzle", "It's not hot: 44°C", "Waiting for your tap" |
| Stop from the tap page | ✅ | Heaters 0, fan 0 afterwards |
| STOP button color on the tap page | info | Red (active) while the page polls the probe. Not checked why: probably `idle_timeout` reads Printing while the endstop queries run (not recorded). Nothing heats or moves. If so, `busy()` in the fork's `ss_setup.py` would also read busy then; today only Start check uses it |

