# Decisions, Questions, Changes and Progress Log

Living record for the Custom Klipper UI/UX project. Newest entries go at the top of each section.
Related: [PLAN.md](PLAN.md)

---

## Progress

| Phase | Status | Notes |
|---|---|---|
| 0. Discovery and safety baseline | 🟡 In progress | ✅ Repo created (StarStackCo/klipper-ui, private). ✅ Local project at Documents\klipper-ui. ✅ SSH key authorised. ✅ **Backup done** (`backups/2026-10-04_1234`, 91 MB, archive verified, SHA256SUMS). ✅ Inventory: CB1 image (Debian 12), Klipper v0.13.0-501, Moonraker v0.10.0, Mainsail v2.17.0, KlipperScreen v0.4.6. ✅ Moonraker access fixed (D-014 applied). ✅ Bench config installed, **Klipper Ready**. ✅ Baseline screenshots (`design/baseline/`). ✅ Regression checklist + Run 0 (`docs/test-checklist.md`). ✅ Remote TFT screenshots working (`scripts/ks-screenshot.sh`). **Phase 0 approved by user 2026-10-04** |
| 1. UX requirements (detail) | ✅ Complete | Answers received. **Requirements v2.1** at `docs/requirements.md`, ✅ **approved by user 2026-10-04**. ✅ KlipperScreen private fork created. ✅ Star mark downloaded Brand sheet received (`design/brand/`) |
| 2. Design | 🟡 In progress | Style directions A/B/C + logo-on-dark options on the design canvas (https://claude.ai/artifact/9P1px8ypq2aYb39NX1BjQc), source in `design/phase2-directions/`. User picked → D-028. **Clickable prototype of all screens** published (artboard "Chosen design"). TFT design **approved** (D-029/D-030). Mainsail theme **built** (`mainsail-theme/`), waiting for deploy approval + Pi back online |
| 3. Build increments (bench) | 🟡 Touchscreen v1 done, waiting for user review | Mainsail theme + macros + touchscreen all on the bench |
| 3.5 Safety review + move to full printer | ⏳ Not started | |
| 4. Polish and handover | ⏳ Not started | |

---

## Open questions

| ID | Date | Question | Why it matters | Status |
|---|---|---|---|---|
| Q-045 | 2026-10-05 | Pi offline again during step 6 (second time on PC USB power). Nothing had run yet | Step 6 waits for the Pi | Answered: back online. **Second hard power loss corrupted ~/KlipperScreen/.git** (empty object). Other repos fsck OK. Fixed by re-clone (damaged copy kept as ~/KlipperScreen.corrupt-20261005-1115). **A dedicated 5V/3A supply is now strongly recommended** before more work |
| Q-044 | 2026-10-04 | **Resume next session (KlipperScreen build).** Done + bench-tested: rail/STOP, Home idle/printing/paused, Print, Controls, Settings, adjust, cancel object, dialogs. Written, NOT yet deployed/tested: in-content prompts (#9), filament color-change mode, readable object names. TODO: (1) Home: color-change countdown alternating with time left (user request, scanner `starstack.scan_color_changes` ready); (2) `M600` macro → PAUSE + "Color change" message (+ safety review); (3) reheat-then-resume when nozzle cooled while paused (Mainsail RESUME aborts otherwise); (4) style ± step buttons; (5) error/shutdown screen; (6) full bench re-tour, then check in with user | Session ended at usage limit | **Resolved 2026-10-05**: all items done and bench-tested (Run 3) |
| Q-043 | 2026-10-04 | User: grey out STOP when no job is running? | Safety: STOP is also needed during homing, jogging, heating, filament changes | Answered: user approved Claude's alternative → D-036 |
| Q-042 | 2026-10-04 | Mainsail macro panels appear alphabetically (Advanced, Filament, Preheat, Speed). Reorder to Speed, Preheat, Filament, Advanced? (dashboard layout DB keys, or drag in Settings › Dashboard) | Polish | Open, low priority |
| Q-041 | 2026-10-04 | Does the localhost Mainsail (http://localhost:8090) still ask for approval on every click in the browser pane? | Whether D-034 fixes the approval friction | Open: user to confirm |
| Q-040 | 2026-10-04 | Real printer: verify the runout sensor pin reads stable (bench pin floated and triggered a phantom pause) | False pauses mid-print | Open, Phase 3.5 checklist item |
| Q-039 | 2026-10-04 | Approve deploying macros v1 + bench config v2.1 + the showZOffset setting to the bench Pi? | Changes on the Pi | Answered: **yes**. User present, approved heating/filament/motion tests |
| Q-038 | 2026-10-04 | Mainsail's Toolhead panel shows **Z-offset babystep** buttons. The TFT has no babystep (D-023). Keep it in Mainsail (advanced web use) or hide it? | Consistency vs power-user access | Answered: **(b) hide**, via Mainsail's own `view.toolhead.showZOffset` setting (no CSS hiding) |
| Q-037 | 2026-10-04 | Pi went offline mid-session (no ping/SSH/HTTP from this PC). Possibly USB power from the PC dropped (sleep?) | Can't deploy or verify until it's back | Answered: back online. Hard power loss (previous boot log ends abruptly), no disk errors, config hashes match the repo. **Recommend a dedicated 5V/3A supply** |
| Q-036 | 2026-10-04 | Approve deploying the Mainsail theme (`.theme` folder) and the 6 Mainsail settings in `mainsail-theme/settings.json`? | Changes on the Pi | Answered: **yes, both** |
| Q-035 | 2026-10-04 | Design choices in the prototype that change requirements v2.1: (a) Advanced tools (extrude, macros, console, limits, updates, restart firmware) live in **Settings › Advanced** instead of Controls, so Controls never scrolls. (b) Print page shows **6 files per page with ‹ › buttons** instead of a scrolling list. (c) Flow dialog has **±1 and ±5** (asked: ±1). (d) Jog uses a fixed **10 mm** step. (e) Pop-ups never cover the left rail, so **STOP is always reachable**, even in dialogs | Needs approval before building | Answered: user approved the whole prototype ("love it all") → D-029 |
| Q-034 | 2026-10-04 | Pick a style direction: A Soft Cards · B Bold Tiles · C Hairline (or a mix), and a logo-on-dark option (1 white plate · 2 pale sky plate · 3 white circle) | Drives every screen design | Answered: **Claude's recommendation** → D-028 |
| Q-033 | 2026-10-04 | Real bed size (X × Y) and max Z height? Bench v2 uses a placeholder 220 × 220 × 250 | The cancel-object bed map should match the real bed | Answered: **180 × 180 × 180 mm** |
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
| Q-020 | 2026-10-04 | Mainsail Temperatures panel is empty, though KlipperScreen shows both sensors | Live data must show in the new UI | Resolved: shows Extruder/Bed with bench v2 |
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
| D-048 | 2026-10-05 | **Step 6 done:** Pi ~/KlipperScreen is a clean clone of the public fork (branch starstack, upstream remote fetch-only). moonraker.conf `[update_manager KlipperScreen]` → fork + `primary_branch: starstack` (backup .pre-ks-fork). Upstream tags pushed to the fork so the version reads v0.4.6-33. Mainsail update manager: valid, not dirty, no warnings. Dev loop is now `scripts/ks-update.sh` (push → Pi fast-forward → restart). `deploy-ks-bench.sh` deprecated. `install-ks-fork.sh` now stops on failure and auto-recovers a corrupt repo | | User | User | **Applied 2026-10-05** |
| D-047 | 2026-10-05 | **Both repos made public** (klipper-ui, KlipperScreen-starstack). Team decision, because the StarStackCo org disables deploy keys org-wide (no per-repo option). Pre-publication audit of full history: no secrets, keys, backups or logs. Public, low risk: LAN IP 192.168.0.102, user `biqu`, file names in screenshots, brand sheet (sam@starstack.com) and logos. Step 6 now uses plain HTTPS (`scripts/install-ks-fork.sh`, with --rollback) | Enable org deploy keys / fine-grained token / public | Simplest to maintain, no credentials on the Pi | User + team | **Applied 2026-10-05** |
| D-046 | 2026-10-05 | Klipper starting/restarting/reconnecting screen restyled: StarStack logo2 plate, spinner, plain status, Details, confirmed Restart Klipper / Retry connection | | User request | User | Applied, bench-tested |
| D-045 | 2026-10-05 | Touchscreen hides routine `echo:` messages (guided screens already show them). Warnings/errors (`!!`) still pop up. Everything stays in the Mainsail console | | User: "hide redundant info" | User | Applied |
| D-044 | 2026-10-05 | Review fixes: rail icons in 5 equal slots (measured ~59 px apart), STOP contents centered. Buttons never gray out while Klipper is busy. Speed presets highlight on tap. Root cause of "speed grays out": a real file on the bench waits forever in M109/M190 (fake heaters) and queues every later command. The same happens briefly during real heat-up | | User review | User | Applied |
| D-043 | 2026-10-05 | **Content guard (safety):** the page area is wrapped in a scroller so no page can push STOP off-screen | | Found in testing (prompt grew window to 478 px) | Claude (safety fix) | Applied |
| D-042 | 2026-10-05 | Klipper shutdown/error → StarStack "Printer stopped / Printer error" page with one confirmed Restart printer (FIRMWARE_RESTART). Startup/connecting keep the stock splash | | Approved design | User (design) | Applied |
| D-041 | 2026-10-05 | Resume when the nozzle cooled while paused: UI reheats to Mainsail's saved print temp, then resumes automatically (tap again to stop waiting) | Let Mainsail's RESUME abort / reheat-then-resume | Consumer-friendly. Avoids the "RESUME aborted" dead end | Claude (UX) | Applied |
| D-040 | 2026-10-05 | Color changes: `M600` macro (→ PAUSE + message). Touchscreen scans the file (M600/M601/PAUSE, M73) and **alternates "Color change in X" / "X left" every 4 s**. Paused at a change → "Change filament" (unload → pull out → load → purge) | | User request | User | Applied |
| D-039 | 2026-10-04 | American spelling in all UI text and docs (color, canceled, gray) | | User | User | Accepted |
| D-038 | 2026-10-04 | **TFT is 16-bit colour (RGB565)**: neutral greys must use multiples of 8 or they tint green (#161616 → #101410). Touchscreen greys snapped: bg #080808, surfaces #181818, rail #101010, lines #282828. Mainsail keeps exact brand values | Exact brand hex / snapped | Visual accuracy on the real panel | Claude (finding) | Applied |
| D-037 | 2026-10-04 | KlipperScreen step 1: `styles/starstack` theme generated by `klipper-ui/scripts/build_ks_theme.py` from `klipperscreen/style.css`. 57 icons → Bootstrap Icons 1.13.1 (recoloured, tagged STARSTACK-ADDED), rest = material-dark. Public Sans 2.001 installed to `~/.local/share/fonts` (no sudo). Bench deploy/rollback: `scripts/deploy-ks-bench.sh` (manifest-based, restarts via Moonraker). Code-marking convention: `STARSTACK-ADDED` / `STARSTACK-CHANGE #n BEGIN/END`, listed in the fork's FORK_CHANGES.md + README notice | | User request: easy maintenance | User | **Deployed to bench 2026-10-04** |
| D-036 | 2026-10-04 | STOP button: **red and prominent whenever anything is active** (printing, paused, any heater target > 0, busy/homing/moving, macro running). **Grey/dimmed when fully idle and cold, but still tappable** (with confirmation). Never disabled or hidden | Disable when idle / always red / dim-but-active | Keeps STOP for homing crashes, heating and filament changes, with a calm look when idle | User | Accepted, to build in step 2 |
| D-035 | 2026-10-05 | Step 6: Pi tracks public fork | fork starstack 6b1225d9 | ✅ Pi | update manager valid/clean, KS active, screenshot ✅ | Repo corruption from power loss found and repaired |
| 2026-10-05 | StarStack touchscreen v1 (steps 2–5) + M600 | fork `starstack` e8a712d9 | ✅ bench | Run 3 ✅ | Content-guard safety fix during testing |
| 2026-10-04 | KlipperScreen theme v1 (step 1) | fork `starstack` 5ce553db → RGB565 fix | ✅ bench (undo: deploy-ks-bench.sh --rollback) | KlipperScreen active, screenshot ✅, colours neutral | Mainsail 'dirty' flag for KlipperScreen expected until the fork install (step 6) |
| 2026-10-04 | Mainsail macro groups (expert mode): **Speed** (always), **Flow** (printing/paused), **Preheat** + **Filament** (idle/paused, Cool down/Done grey), **Advanced** (orange: pause-at-layer, generic PREHEAT). Fixed ids in `mainsail-theme/macrogroups.json`, `scripts/mainsail-macrogroups.sh` (--show/--rollback) | Flat list / groups | Clear one-click buttons by task. Hides buttons that would be refused anyway | User | **Applied 2026-10-04**. Panel order is alphabetical (Advanced first), reorder later |
| D-034 | 2026-10-04 | **Local dev Mainsail on localhost** (user's plan): exact Pi build (v2.17.0) copied read-only to `dev/mainsail/` (git-ignored), `config.json` → 192.168.0.102:7125, served on http://localhost:8090 (python http.server bound to 127.0.0.1, `.claude/launch.json` "mainsail-local"). No Moonraker change needed: cors_domains already has `*://localhost:*`, trusted_clients has 192.168.0.0/24 (the plan's 192.168.1.0/24 was the wrong subnet). Theme + settings load from the printer | Printer IP / localhost | Avoids per-click approval on the printer IP | User | Accepted, working |
| D-033 | 2026-10-04 | Bench config v2.2: runout sensor kept but **disabled at startup** (floating pin caused a phantom pause) | Remove sensor / disable / keep | UI still shows the sensor. Bench only | Claude (fix within the approved test step) | Applied |
| D-032 | 2026-10-04 | Macros v1 (`macros/starstack_macros.cfg`): speed presets, SET_FLOW/FLOW_ADJUST (40–120), PREHEAT(+PLA/PETG/TPU), COOL_DOWN, LOAD/PURGE_MORE/UNLOAD/FILAMENT_DONE with `save_variables` memory, 300 s abandoned-heater timeout, _SS_RUNOUT. **Non-blocking heat** (no M109). Safety review in `docs/macro-safety-review.md` | Blocking M109 flows / non-blocking | A stuck G-code queue can't be cancelled from the UI. Testable on the bench | User | Accepted, **applied 2026-10-04**. 34/34 bench tests |
| D-031 | 2026-10-04 | Mainsail theme = Layer A only: `.theme/custom.css` (brand colours, Public Sans, 10px radius, solid red E-stop, no hidden/moved features), `sidebar-logo.png` + favicons (star mark on a white plate). Plus 6 Mainsail DB settings: primary #00ACC7, logo #88D8F2, **confirm on E-stop**, **confirm on cancel**, **show Cancel print while printing**, dark mode. One-command deploy/rollback scripts | CSS-only vs fork | Survives Mainsail updates (D-005). Safety settings match the TFT | User | Accepted, **applied 2026-10-04** |
| D-030 | 2026-10-04 | Prototype feedback applied: (1) small buttons kept ≥14–16 px from screen edges, minimum 44 px tall; (2) **loaded filament is remembered**, Unload starts immediately for it, Load warns to unload first; (3) **gear icon** for Settings (Bootstrap Icons); (4) Print page **sort button**: Newest → Oldest → Recently printed | n/a | User feedback | User | Accepted, in prototype |
| D-029 | 2026-10-04 | TFT prototype approved, including: Advanced tools in Settings › Advanced, 6 files per page, flow ±1/±5 (40–120%), 10 mm jog, pop-ups never cover the rail/STOP | n/a | User approval | User | Accepted |
| D-028 | 2026-10-04 | Visual direction: **A · Soft Cards** base + **3 recent prints** on idle Home (from C) + labelled **STOP** E-stop (from B). Logo option **1, white plate** | A / B / C / mix | Bambu-like, best fit for reprinting, clearest E-stop. Follows the brand's light-background rule | User | Accepted |
| D-027 | 2026-10-04 | Bench config v2 safety design: real heater pins gpio20/gpio21 never referenced. Fake heaters on logic-only pins gpio19 (servo) / gpio11 (RGB). Pi CPU as the fake sensor. verify_heater relaxed only for the fake heaters. Instant fake homing. Startup BENCH warning. Pins from Mellow FLY-Micro4 docs | Real heater pins + relaxed checks / logic pins | If the bench file ever reaches the real printer, nothing can heat | User | Accepted, **applied 2026-10-04** |
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
| 2026-10-04 | Mainsail macro groups | main (mainsail-theme/macrogroups.json) | ✅ Pi DB (undo: --rollback) | Visual check ✅ | Flow hidden in standby by design |
| 2026-10-04 | Macros v1 + bench v2.1→v2.2 + showZOffset | main (macros/, config/bench/) | ✅ Pi (undo: printer.cfg.bench-v2) | Run 2: 34/34 | Phantom runout found and fixed (v2.2) |
| 2026-10-04 | Mainsail theme v1 (.theme) + 6 UI settings | main (mainsail-theme/) | ✅ Pi (no previous .theme. Undo: --rollback scripts) | Run 1: E-stop confirm ✅, mobile ✅, Klipper ready ✅ | Pi had a hard power loss before deploy. Verified config intact first |
| 2026-10-04 | Bench printer.cfg v2 (cartesian, fake heaters) | main (config/bench/printer.cfg) | ✅ Pi (on-Pi undo copy: printer.cfg.bench-v1) | Klipper **ready**. Fake heaters read 41 °C. All endstops TRIGGERED. Runout = present. TFT shows Extruder/Bed/Extrude/Print | Fixed after first deploy: X endstop + runout pins inverted (pins read low on this board, shared with driver DIAG) |
| 2026-10-04 | Bench printer.cfg v1 | main (config/bench/printer.cfg) | ✅ Pi (on-Pi undo copy: printer.cfg.old-machine) | Klipper **ready**. 0 under-voltage events | MCU temp reads wrong (Q-018) |
