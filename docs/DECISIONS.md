# Decisions, Questions, Changes and Progress Log

Living record for the Custom Klipper UI/UX project. Newest entries go at the top of each section.
Related: [PLAN.md](PLAN.md)

---

## Progress

| Phase | Status | Notes |
|---|---|---|
| 0. Discovery and safety baseline | 🟡 Setting up | Answers received 2026-10-04. Next: SSH + GitHub setup, then config backup |
| 1. UX requirements | ⏳ Not started | |
| 2. Design | ⏳ Not started | |
| 3. Build increments (bench) | ⏳ Not started | |
| 3.5 Safety review + move to full printer | ⏳ Not started | |
| 4. Polish and handover | ⏳ Not started | |

---

## Open questions

| ID | Date | Question | Why it matters | Status |
|---|---|---|---|---|
| Q-011 | 2026-10-04 | Exact GitHub account name (what is "sam@starstack": a username, an org, or an email?) and the repo name (proposed `klipper-custom-ui`) | Repo creation | Open |
| Q-010 | 2026-10-04 | BTT Pi IP address/hostname and SSH username (BTT image default is `biqu`) | SSH setup | Open |
| Q-009 | 2026-10-04 | OK to install GitHub CLI (`gh`) with winget? | GitHub workflow | Open |
| Q-008 | 2026-10-04 | Which folder on this PC should hold the project and the backups? | Scratch workspace is temporary | Open |
| Q-007 | 2026-10-04 | Bench testing without a mainboard: is it worth adding a separate "bench" Klipper config so Klipper reaches Ready? | More UI states testable on the bench | Open, decide in Phase 0 |
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
| D-010 | 2026-10-04 | Testing in two stages: bench (Pi + screen on 5V USB) for building, then the full printer only after a safety review | Test on full printer from day one / bench first | Safer, and the user's preference | User | Accepted |
| D-009 | 2026-10-04 | First task is backing up the current config (config folder, Moonraker DB, KlipperScreen.conf) to this PC, read-only on the Pi | n/a | The 8 GB initial image is outdated | User | Accepted |
| D-008 | 2026-10-04 | Claude connects with Windows' built-in OpenSSH using key-based login (no stored passwords). The user keeps MobaXterm for their own use | MobaXterm / OpenSSH + keys | Claude can't drive a GUI terminal. Keys mean Claude never handles the Pi password | Proposed | Pending approval |
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
| | | | | | |
