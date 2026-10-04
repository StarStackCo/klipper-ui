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
