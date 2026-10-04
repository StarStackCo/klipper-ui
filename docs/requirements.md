# Phase 1: UX Requirements

**Status:** DRAFT v1, 2026-10-04. Built from the user's answers. Items marked **❓** need a decision (see DECISIONS.md).

## 1. Who and how

- **Product framing:** a *consumer* printer. Usable by anyone without training (StarStack's audience includes students and teachers). Simple by default, with an **Advanced mode** toggle that reveals power-user controls.
- **Main workflow:** slice in **OrcaSlicer** → send to printer → monitor on TFT/Mainsail.
- **TFT is used for:** reprinting a previous job, cancelling a job, **cancelling individual objects** mid-print, live tuning, filament load/unload.
- **Mainsail is used for:** everything above, plus advanced work (input shaping, config) under advanced settings.
- **Out of scope for the UI:** bed meshing and print-start sequences (handled by Klipper + Orca start G-code). **No Z offset UI**: nozzle-contact probing (E3D PZ) has no offset.
- **Hardware now/planned:** filament runout sensor (planned). No LEDs, camera or enclosure for now.

## 2. TFT navigation model (480 × 320)

User requirement: **single left column of 4–5 icons** to switch pages. Every page fits on one screen with no scrolling and no "more" tabs. Exception: **Settings may scroll**. The first icon is the main page.

Proposed rail (top → bottom):

| # | Icon | Page | Purpose |
|---|---|---|---|
| 1 | Home | **Home** | Printer status. Idle: reprint last + recent prints + preheat. Printing: live job card |
| 2 | Files | **Print** | Browse/print files with thumbnails |
| 3 | Sliders | **Controls** | Temperatures, fan, filament, movement |
| 4 | Gear | **Settings** | Scrollable list. Contains the Advanced mode toggle |
| — | ⛔ | **E-stop** | Pinned at the bottom, red, **always visible** (baseline finding D-016) |

## 3. Action inventory (draft)

Legend: **N** = Normal mode · **A** = Advanced mode only · 🔒 = locked while printing · ⚠️ = needs confirmation · Where: T = TFT, M = Mainsail

### Home: idle
| Action | Mode | Where | Notes |
|---|---|---|---|
| Reprint last job | N ⚠️ | T M | Confirm: **"Is the bed clear?"** |
| Recent prints (thumbnails), tap to reprint | N ⚠️ | T M | Same bed-clear confirmation |
| Preheat PLA / PETG / TPU | N | T M | One tap. Sets nozzle + bed |
| Cool down | N | T M | |
| Printer status (temps, state) | N | T M | |

### Home: printing
| Action | Mode | Where | Notes |
|---|---|---|---|
| Thumbnail, progress %, time left, layer x/y | N | T M | |
| Pause / Resume | N | T M | |
| Cancel print | N ⚠️ | T M | |
| **Cancel object** (pick from list/map) | N ⚠️ | T M | Requires `[exclude_object]` + Orca "Label objects" |
| Speed preset: **Silent 50% · Normal 100% · Fast ❓ · Draft ❓** | N | T M | Macro chips |
| Nozzle / bed target temperature | N | T M | Clamped to config limits |
| Part fan % | N | T M | |
| Flow % | N | T M | Clamped range ❓ |
| Z babystep | A | T M | Optional first-layer rescue ❓ |
| Pressure advance | A | T M | |

### Print (files)
| Action | Mode | Where | Notes |
|---|---|---|---|
| File list with thumbnails, newest first | N | T M | |
| Print file | N ⚠️ | T M | Bed-clear confirmation |
| Delete file | N ⚠️ | T M | |

### Controls
| Action | Mode | Where | Notes |
|---|---|---|---|
| Nozzle / bed temperature + material presets | N | T M | |
| Part fan | N | T M | |
| **Load filament**: pick material → heats to the right temp → load → purge → "Purge more / Done" | N | T M | 🔒 while printing (runout flow handles mid-print changes) |
| **Unload filament**: pick material → heat → unload | N | T M | 🔒 |
| Home all | N | T M | 🔒 |
| Move axes (jog) | N | T M | 🔒 |
| Disable motors | N | T M | 🔒 |
| Extrude / retract by amount | A | T M | Blocked when cold |
| Macros list | A | T M | |
| Console | A | T M | |
| Velocity/accel limits | A | T M | |

### Settings (scrollable)
| Action | Mode | Where | Notes |
|---|---|---|---|
| **Advanced mode** on/off | N | T M | ❓ protect with PIN? |
| Wi-Fi / network | N | T | |
| Screen brightness / sleep | N | T | |
| Language, units, 24h time | N | T | |
| Updates | A | T M | |
| Restart firmware / Klipper | A ⚠️ | T M | |
| Shutdown / reboot host | N ⚠️ | T M | 🔒 while printing |
| System info (versions, IP) | N | T M | |
| Input shaping, bed mesh view, config editor | A | M | User does these in Mainsail |

### Event-driven
| Event | Flow |
|---|---|
| Filament runout (future sensor) | Auto-pause → "Filament ran out" screen → guided unload/load → Resume |
| Print finished | "Done" card → **Print again** (bed-clear confirm) / Dismiss |
| Error / shutdown | Full-screen red state with plain-language message + "Restart" (⚠️) |
| Heaters idle | Klipper `[idle_timeout]` turns heaters off. UI shows the countdown |

## 4. Printer-state rules

| State | Rules |
|---|---|
| Idle | Everything available (per mode) |
| Heating | All available. Show progress to target |
| Printing | Motion, homing, filament load/unload, shutdown **locked**. Temps/fan/flow/speed editable |
| Paused | Resume/Cancel prominent. Filament change allowed |
| Error/shutdown | Only status, Restart, E-stop. Everything else disabled |

## 5. Things the real printer config must include (for Phase 3.5)

`[exclude_object]`, `[pause_resume]`, `[virtual_sdcard]`, `[display_status]`, `[idle_timeout]`, `[filament_switch_sensor]` (when fitted), `min_extrude_temp`, `[verify_heater]` defaults left as they are.

## 6. OrcaSlicer settings to check

- **Label objects** ON and **Exclude objects** ON (needed for cancel object)
- **Thumbnails** in a Klipper-readable format (e.g. `48x48/PNG, 300x300/PNG`)
- Start G-code passes bed/nozzle temps to `PRINT_START`
