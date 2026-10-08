# Custom Klipper UI/UX: Project Plan

**Status:** Approved 2026-10-04. Phases 0–3.5 done; Phase 4 (polish and handover) in progress. Updated 2026-10-08.
**Created:** 2026-10-04
**Companion doc:** [DECISIONS.md](DECISIONS.md) (decisions, questions, changes, progress)

---

## 1. Goal

Design and build one consistent, good-looking custom UI/UX for two surfaces:

1. **On-printer touchscreen:** BTT TFT35
2. **Web UI:** Mainsail, running on the BTT Pi

Every user task needs a button. Nothing we ship may weaken printer safety or break an existing workflow. Work happens in small steps, gets tested on the real printer, and is pushed to GitHub as each part is finished.

## 2. Hardware and software stack

| Part | Role | What we customise |
|---|---|---|
| **BTT Pi** (CB1, network name `starstack-s1`) | Host: Klipper, Moonraker, Mainsail, KlipperScreen | UI files, themes, configs. OS-level changes only where agreed: USB import, boot screen, faster boot (D-067..D-080), network name (D-085) |
| **FLY Micro4** | Mainboard running Klipper MCU firmware | Macros (each one safety-reviewed) and the S1 `printer.cfg`. Firmware only to keep it at the host's Klipper version, through its Katapult bootloader (changed 2026-10-07, D-083) |
| **BTT TFT35 SPI** | Touchscreen on the Pi's GPIO. The Pi draws it using **KlipperScreen** | The StarStack fork of KlipperScreen (StarStack screens + theme, D-026, D-047) |

**Printer:** the **StarStack S1**, a cantilevered bed-slinger (180 × 180 × 165 mm) with an E3D PZ probe, E3D Revo Voron 40 W and Galileo 2 extruder, sensorless X/Y. Config: `config/s1/printer.cfg` (D-081, D-084).

**Target feel:** close to modern consumer printers (Bambu-style): simple, large, friendly main screens, with an **advanced layer** for power users. (See D-006.)

### Test environments
1. **Bench:** BTT Pi + TFT35 SPI on 5V USB power, with no mainboard connected. Used for all build and test work. Klipper will report the MCU as disconnected, so any feature that needs a running printer gets tested in stage 2.
2. **Full printer:** only after a safety review of everything built (Phase 3.5 below). ✅ Since 2026-10-07 the board and Pi run the S1.

## 3. Guiding principles

1. **Safety first.** Klipper's config (`max_temp`, `min_extrude_temp`, endstops, thermal runaway protection) stays the final authority. The UI never bypasses it.
2. **Customisation layers, least invasive first.** We use the lightest layer that does the job:
   - **Layer A, Theme/config only.** Mainsail `.theme/` folder (custom.css, logos, background) and KlipperScreen theme + `KlipperScreen.conf` menus. Survives updates, nearly zero risk.
   - **Layer B, Macros and layout.** Custom macros (e.g. load/unload filament, preheat profiles), dashboard layout, macro groups, presets.
   - **Layer C, Code forks.** Forked Mainsail and/or KlipperScreen with new components. **You'd prefer to avoid this.** We only consider it if A/B can't deliver something you really want, and I'll ask first each time. *Used once, approved: the KlipperScreen fork (D-026), because the touchscreen redesign isn't possible with themes and menus alone. Mainsail stays unforked.*
3. **One design system, two screens.** Shared colours, icons, naming and interaction rules, adapted to a 480×320 touchscreen and a desktop/phone browser.
4. **Nothing is lost.** Every action in today's UI is mapped to a place in the new one before we remove or move it.
5. **Easy to undo.** Every deploy has a documented one-step rollback.

## 4. Phases

Each phase ends with a **checkpoint**: I stop, show you the result, and wait for your approval before going on. Everything gets logged in DECISIONS.md.

### Phase 0: Discovery and safety baseline ✅ done 2026-10-04
- **Step 1, back up first** (your priority). Copy the whole current `~/printer_data/config` folder, the Moonraker database (which holds Mainsail settings) and `KlipperScreen.conf` from the Pi to this PC. Read-only on the Pi, so nothing there changes. Your old 8 GB image is out of date, so this backup is the real safety net.
- Confirm the OS image and the versions of Klipper, Moonraker, Mainsail and KlipperScreen.
- Create the GitHub repo and folder structure (section 5).
- Record the "before" state: screenshots of the current UI and a list of current macros.
- Write the **baseline regression checklist** (section 6), run it once on the current setup, and record the results.
- ✅ Checkpoint: baseline confirmed, backup verified, repo created.

### Phase 1: UX requirements (what you need to do, and where) ✅ done 2026-10-04
- Map your real workflows: power-on/preheat, bed levelling/mesh, Z offset, filament load/unload/change, start print, monitor print, pause/resume/cancel, tuning during a print (speed, flow, fan, Z babystep), failure recovery, maintenance, updates/shutdown.
- Build an **action inventory**: every button/action, which screen it belongs on (TFT, Mainsail or both), how often it's used, and whether it's dangerous and needs a confirmation step.
- Define **printer-state rules**: what's shown, enabled or locked while idle, heating, printing, paused or in error. Example: no axis jogging during a print, and Emergency Stop always visible.
- ✅ Checkpoint: you approve the action inventory and state rules.

### Phase 2: Design (together) ✅ done 2026-10-05
- **Mood/style direction:** I'll show 2–3 visual directions as clickable previews and you pick one or mix them.
- **Design system:** colour palette (with clear danger/warning/heat colours), typography, icon set, spacing, touch-target sizes (minimum ~48px on the TFT), dark/light.
- **TFT screens:** wireframes, then hi-fi mockups at 480×320 for each screen in the navigation map.
- **Mainsail:** mockups of the dashboard, panels, sidebar, and the mobile layout.
- Usability walk-through: step through each Phase 1 workflow on the mockups and count taps/clicks.
- ✅ Checkpoint: you sign off the designs screen by screen.

### Phase 3: Build in increments (each increment = branch, review, test, merge, push) ✅ released (touchscreen v1, Mainsail theme, macros, boot screen, USB import)
Proposed order, lowest risk first:
1. **Mainsail theme** (Layer A): colours, fonts, logo, background.
2. **Touchscreen theme** (Layer A): colours, icons, fonts.
3. **Touchscreen menus/navigation** (Layer A/B): restructured to the approved nav map.
4. **Macros** (Layer B): new or cleaned-up macros behind the new buttons. Each gets a safety review.
5. **Mainsail layout/presets/macro groups** (Layer B).
6. **Custom components/panels** (Layer C, only if needed and approved).

For every increment:
- Branch, implement, and run a self-review against the safety checklist.
- I show you screenshots/preview **before** it goes on the printer.
- Deploy to the printer (with your OK), then run the regression checklist.
- Merge, push to GitHub, and update DECISIONS.md progress.

### Phase 3.5: Safety review, then move to the full printer ✅ done 2026-10-08 (first print OK)
- Full safety review of every macro and every UI action, recorded in DECISIONS.md.
- You move the Pi to the full printer. We test in stages: Klipper connects and there are no errors, then heaters with low targets, then homing and movement, then probe and Z offset, then a test print.
- ✅ Checkpoint: you approve each stage before the next.

### Phase 4: Polish and handover 🟡 in progress
- Full regression run, including a real test print.
- ✅ Install/update docs in the repo README (one-tap updates, pinning, releasing).
- ✅ Repo registered with Moonraker's `update_manager` (install.sh step 3).
- 🟡 One-tap updates with tested versions and board firmware (D-087): built and tested on the S1; update helper service installed and running on the S1; left: release v0.2.0 (D-088).
- ✅ Start of print that never blocks Cancel (`PRINT_START`, D-089): all tests passed on the S1.
- Open: filament check before printing (Q-052), update safety (Q-053).
- Still to do: Wi-Fi on the S1 with the antenna (B-6), starter prints (B-8, last), camera switch when a camera is fitted (B-9). See [BACKLOG.md](BACKLOG.md).

## 5. Repo structure (as built)

- `StarStackCo/klipper-ui` (GPL-3.0, public since D-047): `install.sh`, `macros/`, `mainsail-theme/`, `config/` (`s1/`, `bench/`), `splash/`, `boot/`, `usb/`, `tools/`, `scripts/`, `design/`, `docs/`
- `StarStackCo/KlipperScreen-starstack` (AGPL-3.0, public copy with upstream as a remote): StarStack screens (`panels/ss_*`, `ks_includes/starstack*.py`), theme source and tools in `tools/starstack/`, change log `FORK_CHANGES.md`
- Branches: stable `main` / `starstack` (what printers install), work on `dev`

## 6. Safety and regression checklist (runs on every increment)

**Safety, must always pass:**
- [ ] Emergency Stop can be reached from every screen on both UIs, at most 1 tap/click away.
- [ ] Cancel print, firmware restart, shutdown and reboot ask for confirmation.
- [ ] Axis moves and homing are disabled or locked while printing.
- [ ] Heater inputs can't go past configured limits, and the UI shows real values reported by Klipper.
- [ ] New macros don't change or bypass `max_temp`, `min_extrude_temp`, thermal runaway protection or endstops.
- [ ] Extrude/retract is blocked or warned when the hotend is cold.
- [ ] Error/shutdown states are obvious (colour + text, not colour alone).
- [ ] No passwords, API keys or private network info committed to GitHub.

**Functional, nothing broken:**
- [ ] Klipper starts with no config errors and Moonraker connects.
- [ ] Both UIs load. Temps, position and print progress update live.
- [ ] Home, jog, preheat, cooldown, fan, load/unload filament.
- [ ] Upload file, start, pause, resume, cancel.
- [ ] Live tuning: speed, flow, Z babystep.
- [ ] Bed mesh and Z offset workflows.
- [ ] Mobile Mainsail layout is usable.
- [ ] Rollback script restores the previous state.

## 7. How we work together
- I **stop and ask** whenever something is unclear. No guessing on anything that affects safety or your workflow.
- Every decision, question, change and milestone gets logged in **DECISIONS.md**.
- Nothing gets deployed to the printer or pushed to GitHub without your OK for that step.
- Designs get shown as previews before any code is written.

## 8. Risks

| Risk | Mitigation |
|---|---|
| Upstream Mainsail/KlipperScreen updates break customisations | Prefer Layer A/B. Pin versions for forks. Re-run regression after updates. |
| Weak 5V USB supply on the bench browns out the Pi and corrupts the SD card | Back up first. Use a good 5V/3A supply. Check `vcgencmd`/dmesg for under-voltage. |
| Bench can't show "printing" states with no mainboard | Mock-ups for design. Real-state testing in Phase 3.5. |
| A macro does something unsafe | Safety review checklist plus a dry run with heaters off, before any live test. |
| Bad deploy leaves the printer unusable | Backup first, plus a one-command rollback script. |
| Moving buttons breaks your muscle memory | Action inventory and walk-throughs before building. |
