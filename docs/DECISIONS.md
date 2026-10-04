# Decisions, Questions, Changes and Progress Log

Living record for the Custom Klipper UI/UX project. Newest entries go at the top of each section.
Related: [PLAN.md](PLAN.md)

---

## Progress

| Phase | Status | Notes |
|---|---|---|
| 0. Discovery and safety baseline | 🟡 In progress | ✅ Repo created (StarStackCo/klipper-ui, private). ✅ Local project at Documents\klipper-ui. ✅ SSH key authorised. ✅ **Backup done** (`backups/2026-10-04_1234`, 91 MB, archive verified, SHA256SUMS). ✅ Inventory: CB1 image (Debian 12), Klipper v0.13.0-501, Moonraker v0.10.0, Mainsail v2.17.0, KlipperScreen v0.4.6. ✅ Moonraker access fixed (D-014 applied). ✅ Bench config installed, **Klipper Ready**. ✅ Baseline screenshots (`design/baseline/`). ✅ Regression checklist + Run 0 (`docs/test-checklist.md`). ✅ Remote TFT screenshots working (`scripts/ks-screenshot.sh`). **Phase 0 approved by user 2026-10-04** |
| 1. UX requirements (detail) | 🟡 In progress | Answers received. **Requirements v2.1** at `docs/requirements.md`, waiting for approval. ✅ KlipperScreen private fork created. ✅ Star mark downloaded Brand sheet received (`design/brand/`) |
| 2. Design | ⏳ Not started | |
| 3. Build increments (bench) | ⏳ Not started | |
| 3.5 Safety review + move to full printer | ⏳ Not started | |
| 4. Polish and handover | ⏳ Not started | |

---

## Open questions

| ID | Date | Question | Why it matters | Status |
|---|---|---|---|---|
| Q-033 | 2026-10-04 | Real bed size (X × Y) and max Z height? Bench v2 uses a placeholder 220 × 220 × 250 | The cancel-object bed map should match the real bed | Open |
| Q-032 | 2026-10-04 | Logo/star mark on a dark background: the charcoal star `#2E2E2E` disappears on `#0A0A0A` | Brand sheet says light backgrounds only | Open, Phase 2 design options |
| Q-031 | 2026-10-04 | Is there a true vector (SVG paths) version of the star mark? | Sharp icons at any size | Open, nice-to-have |
| Q-030 | 2026-10-04 | Should the KlipperScreen fork be **public** (GitHub forks of public repos are always public) or a **private copy** with KlipperScreen as an upstream remote? | Visibility of the StarStack theme/code | Answered: **(b) private copy**. Created `StarStackCo/KlipperScreen-starstack` |
| Q-029 | 2026-10-04 | Can Claude use the user's cloud computing credit to avoid hitting the 5-hour usage limit? | Session continuity | Answered by Claude: not possible from inside the session. See the 2026-10-04 reply |
| Q-028 | 2026-10-04 | Can Claude download `stars.svg` from starstack.com? | Star mark for the rail, boot screen and favicon | Answered: yes. Downloaded (56 KB, no scripts). Note: it's a raster PNG inside an SVG, not a true vector |
| Q-027 | 2026-10-04 | Logo files `logo2.png` and `logo.png` on Google Drive return **401 (not shared publicly)**. `stars.svg` and the Public Sans link work | Need the real logo files | Answered: use **logo2 only** (user attached it, saved as `design/brand/logo2.png`, 1590×358). Do not use `logo` |
| Q-026 | 2026-10-04 | Bench config v2 (cartesian) needs the FLY Micro4 pinout. Fake heaters must use **non-heater pins**, so the bench config can never heat a real heater if the board moves to the printer | Safety | Open: Claude to research Mellow docs and propose |
| Q-025 | 2026-10-04 | E-stop: single tap, or tap + confirm? | Accidental stops vs speed in an emergency | Answered: **tap, then confirm** |
| Q-024 | 2026-10-04 | Should Advanced mode be PIN-protected (classroom use)? | Students could change PA/limits | Answered: **no PIN**. Show a "proceed at your own risk" confirmation when turning it on |
| Q-023 | 2026-10-04 | Fast and Draft speed % values? Speed only (M220), or also acceleration? | Preset macros | Answered: Fast **125%**, Draft **150%**. Speed % only (M220), as fixed buttons |
| Q-022 | 2026-10-04 | Load temps per material (proposed nozzle/bed: PLA 210/60, PETG 240/80, TPU 225/50) | Filament + preheat macros | Answered: as proposed, except **TPU bed 40 °C** |
| Q-021 | 2026-10-04 | **KlipperScreen's left rail is hard-coded** (`panels/base_panel.py`: back, home, E-stop **only while printing**, shutdown). Custom panels load only from KlipperScreen's own `panels/` folder. The requested TFT design needs a **KlipperScreen fork** (Layer C) | D-005 said Layer C only if unavoidable and approved | Answered: **fork approved**. Every change documented so upstream can always be merged |
| Q-020 | 2026-10-04 | Mainsail Temperatures panel is empty, though KlipperScreen shows both sensors | Live data must show in the new UI | Open, investigate during the Mainsail theme work |
| Q-019 | 2026-10-04 | Browser pane asks for approval on every action for `http://192.168.0.102` ("site-level permissions disabled") | Slows down visual checks | Open. Workaround: navigate by URL instead of clicking. User may check the desktop app's settings |
| Q-018 | 2026-10-04 | The Micro4's MCU temperature reads **-22.9 °C**, which is clearly wrong (Pi reads 39.8 °C) | Display-only sensor, no safety role. Either fix (possibly via a firmware update) or remove it from the UI | Open, low priority |
| Q-017 | 2026-10-04 | Micro4 firmware is **v0.12.0-401**, host Klipper is **v0.13.0-501**. It connects and works, but versions should match before the full printer | Mismatches can cause subtle bugs. Reflashing means touching the board (D-001 covers config, not firmware updates) | Open, decide before Phase 3.5 |
| Q-016 | 2026-10-04 | Is the connected RP2040 `E6647C7403679636` the FLY Micro4? (The old config pointed at a different RP2040 toolboard, `E660D051131C442C`) | The bench config must point at the right board | Answered: **yes, it's the FLY Micro4** (also RP2040). The old config was for a different board |
| Q-015 | 2026-10-04 | Moonraker access: any IP or home network only? | Security | Answered: **home network only** → D-014 |
| Q-014 | 2026-10-04 | Is Klipper firmware already flashed on the FLY Micro4? (Visible once it's plugged in by USB) | Without it there's no MCU ID and it needs flashing | Open, checked on connect |
| Q-013 | 2026-10-04 | The new printer.cfg needs real hardware details: which driver/port does each motor use, thermistor types, heater wiring, PZ probe pin, bed size, rotation distances | The old config was for another machine. A wrong pin or thermistor type is a safety problem | Open, needed before the full-printer phase |
| Q-012 | 2026-10-04 | Bench power is from the PC's USB port. These can supply as little as 0.5–0.9 A, while the Pi + TFT35 + mainboard may draw more | Under-voltage can corrupt the SD card | Mitigation: check `dmesg` for under-voltage after connecting |
| Q-011 | 2026-10-04 | GitHub account/org and repo name | Repo creation | Answered: org **StarStackCo**, repo **klipper-ui** (private) |
| Q-010 | 2026-10-04 | BTT Pi IP and SSH username | SSH setup | Answered: 192.168.0.102, default user `biqu` |
| Q-009 | 2026-10-04 | Install GitHub CLI? | GitHub workflow | Answered: already installed (v2.102.0) and logged in as Sam-Kudarauskas. Nothing installed |
| Q-008 | 2026-10-04 | Project folder? | Scratch workspace is temporary | Answered: `C:\Users\Sam\Documents\klipper-ui` |
| Q-007 | 2026-10-04 | Bench testing without a mainboard? | More UI states testable on the bench | Answered: user will connect the FLY Micro4 with nothing plugged into it → D-012 |
| Q-006 | 2026-10-04 | Is the current config backed up anywhere? | Safety baseline | Answered: only an old 8 GB initial image. Config has changed since, so a backup is needed first |
| Q-005 | 2026-10-04 | Printer details | Which buttons/panels are needed | Partly answered: cantilevered bed-slinger, E3D PZ probe. Still to confirm in Phase 1: filament sensor, LEDs, camera, etc. |
| Q-004 | 2026-10-04 | Customisation depth | Scope | Answered → D-005 |
| Q-003 | 2026-10-04 | SSH access for Claude? | Deploy/test workflow | Answered: yes → D-008 |
| Q-002 | 2026-10-04 | Project location / GitHub repo | Repo setup | Answered: new **private** repo under the user's "starstack" GitHub (exact name → Q-011) |
| Q-001 | 2026-10-04 | Which TFT35 variant? | Touchscreen approach | Answered: **TFT35 SPI** → D-004 |

---

## Decisions

| ID | Date | Decision | Options considered | Rationale | Decided by | Status |
|---|---|---|---|---|---|---|
| D-027 | 2026-10-04 | Bench config v2 safety design: real heater pins gpio20/gpio21 never referenced. Fake heaters on logic-only pins gpio19 (servo) / gpio11 (RGB). Pi CPU as the fake sensor. verify_heater relaxed only for the fake heaters. Instant fake homing. Startup BENCH warning. Pins from Mellow FLY-Micro4 docs | Real heater pins + relaxed checks / logic pins | If the bench file ever reaches the real printer, nothing can heat | Claude (proposed) | Waiting for approval |
| D-026 | 2026-10-04 | KlipperScreen fork = **private copy** `StarStackCo/KlipperScreen-starstack`. Branch `starstack` based on `f580242e` (the Pi's version). `master` mirrors upstream. Upstream push disabled. LF line endings. Changes tracked in `FORK_CHANGES.md` | Public fork / private copy | User choice | User | Accepted, created |
| D-025 | 2026-10-04 | Advanced mode: no PIN. A "proceed at your own risk" confirmation when enabling | PIN / confirm | User | User | Accepted |
| D-024 | 2026-10-04 | Flow control: ±1% buttons, hard cap 40–120% | | User | User | Accepted |
| D-023 | 2026-10-04 | No Z babystep in the UI. No idle-timeout logic in the UI (printer config handles it, the UI only displays it) | | User | User | Accepted |
| D-022 | 2026-10-04 | Cancel object shows a **bed map with object positions + part-name list** | List only / map + list | User | User | Accepted |
| D-021 | 2026-10-04 | **Single dark theme** only | Dark+light / dark only | User | User | Accepted |
| D-020 | 2026-10-04 | KlipperScreen will be **forked** to StarStackCo with minimal changes, documented in `FORK_CHANGES.md` for upstream merges. Mainsail stays code-free | Config only / fork | Requested design is impossible without code (Q-021) | User | Accepted |
| D-019 | 2026-10-04 | Brand: StarStack Brand Sheet v1.0 (colours, Public Sans, 10px radius, 4px spacing, Bootstrap Icons) is the design-system source | n/a | User supplied | User | Accepted |
| D-018 | 2026-10-04 | Bench config v2 will use **cartesian kinematics** so every TFT button appears | none / cartesian | User request | User | Accepted, design pending (Q-026) |
| D-017 | 2026-10-04 | Requirements captured in `docs/requirements.md`: consumer-first, Advanced toggle, 4-icon rail + always-visible E-stop, Settings may scroll, speed presets, material-aware load/unload, cancel object, bed meshing/Z offset out of scope | n/a | User answers | User | Draft, waiting for approval |
| D-016 | 2026-10-04 | Baseline finding: KlipperScreen has **no visible E-stop on the idle home screen**. The new design must show E-stop on every screen (checklist S1) | n/a | Safety | Claude (finding) | For design phase |
| D-015 | 2026-10-04 | Bench config v1 (`config/bench/printer.cfg`): Micro4 only, `kinematics: none`, no heaters/steppers/fans/pins. Read-only MCU + Pi temperature sensors. Old printer.cfg/toolboard.cfg/macros.cfg not included | Reuse old cfg / minimal bench cfg | Nothing wired = nothing to drive. Avoids false thermal shutdowns | User | Accepted, **applied 2026-10-04** |
| D-014 | 2026-10-04 | Moonraker `trusted_clients`: localhost + `192.168.0.0/24` + IPv6 link-local only. Remove the old entries, including `192.168.1.0/24` (wrong subnet, the actual reason Mainsail was refusing the PC) and `128.113.138.0/24` (a public internet range) | Allow all / home only | User choice. Least exposure | User | Accepted, **applied 2026-10-04** (PC gets HTTP 200) |
| D-013 | 2026-10-04 | Printer backups stay on this PC only (`backups/` is git-ignored). Only reviewed, cleaned config goes to GitHub | Push everything / local only | Configs can contain network details and keys | Claude (safety default) | Accepted |
| D-012 | 2026-10-04 | Bench = BTT Pi + TFT35 SPI + FLY Micro4 with nothing connected to the mainboard. A **bench config** gets written with no heaters/thermistors/steppers active, so Klipper reaches Ready without false thermal errors. The real printer config is written separately and safety-reviewed before Phase 3.5 | Use old config / bench config | Old config is for another machine. Unplugged thermistors would trigger errors | User + Claude | Accepted |
| D-011 | 2026-10-04 | Old config is backed up but **not reused** as the base for the new setup | Reuse / start fresh | User: it was for a different machine | User | Accepted |
| D-010 | 2026-10-04 | Testing in two stages: bench (Pi + screen on 5V USB) for building, then the full printer only after a safety review | Test on full printer from day one / bench first | Safer, and the user's preference | User | Accepted |
| D-009 | 2026-10-04 | First task is backing up the current config (config folder, Moonraker DB, KlipperScreen.conf) to this PC, read-only on the Pi | n/a | The 8 GB initial image is outdated | User | Accepted |
| D-008 | 2026-10-04 | Claude connects with Windows' built-in OpenSSH using a project-only key (`~/.ssh/klipper_ui_ed25519`). The user keeps MobaXterm for their own use | MobaXterm / OpenSSH + keys | Claude can't drive a GUI terminal. Keys mean Claude never handles the Pi password. Revoke by deleting the `claude-klipper-ui` line in `~/.ssh/authorized_keys` | User | Accepted |
| D-007 | 2026-10-04 | GitHub: new **private** repo. The user logs in themselves (browser/`gh auth login --web`). Claude never enters credentials | n/a | Security rule | User | Accepted |
| D-006 | 2026-10-04 | Design direction: modern consumer feel (Bambu-style), simple main screens, plus an advanced layer for power users | n/a | User requirement | User | Accepted |
| D-005 | 2026-10-04 | Fully replace themes, menus and macros. Avoid code changes to Mainsail/KlipperScreen if possible (Layers A/B). Layer C only if unavoidable and approved | n/a | Survives updates, user preference | User | Accepted |
| D-004 | 2026-10-04 | Touchscreen = TFT35 SPI driven by **KlipperScreen** on the BTT Pi | KlipperScreen / TFT firmware | Confirmed hardware variant | User | Accepted |
| D-003 | 2026-10-04 | Nothing is deployed to the printer or pushed to GitHub without explicit approval for that step | n/a | User requirement | User | Accepted |
| D-002 | 2026-10-04 | Use customisation layers, least invasive first (A theme → B macros/layout → C forks) | Fork-first / layered | Survives updates, lower risk | User | Accepted (via D-005) |
| D-001 | 2026-10-04 | Mainboard (FLY Micro4) firmware won't be modified. Only macros change, each with a safety review | Modify / don't modify | The UI doesn't need it, and it removes a major safety risk | Proposed | Pending approval |

---

## Changes (plan/scope changes)

| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-04 | Touchscreen path fixed to KlipperScreen. TFT firmware options removed | TFT35 SPI confirmed | User |
| 2026-10-04 | Added Phase 3.5 (safety review + staged move to the full printer) and the bench test environment | User's bench-first approach | User |
| 2026-10-04 | Phase 0 now starts with the config backup | User priority | User |
| 2026-10-04 | Initial plan drafted | Project kickoff | n/a |

---

## Build / deploy log

| Date | Increment | Branch/PR | Deployed? | Regression result | Notes |
|---|---|---|---|---|---|
| 2026-10-04 | Moonraker trusted_clients → 192.168.0.0/24 | main (config/pi/moonraker.conf) | ✅ Pi (on-Pi undo copy: moonraker.conf.pre-klipper-ui) | Moonraker restart OK, no warnings. PC → HTTP 200 | Fixes Mainsail access |
| 2026-10-04 | Bench printer.cfg v1 | main (config/bench/printer.cfg) | ✅ Pi (on-Pi undo copy: printer.cfg.old-machine) | Klipper **ready**. 0 under-voltage events | MCU temp reads wrong (Q-018) |
