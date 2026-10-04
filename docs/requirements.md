# Phase 1: UX Requirements

**Status:** DRAFT v2, 2026-10-04. Waiting for user approval. Items marked **❓** are still open (see DECISIONS.md).
**Changes from v1:** answers to round 2 applied (see the change list at the bottom).

## 1. Who and how

- **Product framing:** a *consumer* printer. Usable by anyone without training (StarStack's audience includes students and teachers). Simple by default, with an **Advanced mode** toggle that reveals power-user controls.
- **Main workflow:** slice in **OrcaSlicer** → send to printer → monitor on TFT/Mainsail.
- **TFT is used for:** reprinting a previous job, cancelling a job, **cancelling individual objects** mid-print, live tuning, filament load/unload.
- **Mainsail is used for:** everything above, plus advanced work (input shaping, config) under advanced settings.
- **Out of scope for the UI:**
  - Bed meshing and print-start sequences (handled by Klipper + Orca start G-code).
  - **Z offset and Z babystep.** Nozzle-contact probing (E3D PZ) has no offset, and the user chose no babystep.
  - **Heater idle timeout.** Already handled by the printer config. The UI only *displays* it.
- **Hardware now/planned:** filament runout sensor (planned). No LEDs, camera or enclosure for now.

## 2. Look and feel

- **One dark theme only** (no light mode), built from the StarStack Brand Sheet v1.0:
  - Background `#0A0A0A`, surfaces `#161616`, borders `#282828`, text `#FAFAFA`, muted text `#A1A1A1`
  - Button fill: Site Primary `#0D3C96`. Highlights/selected/focus: Accent `#00ACC7` and Star Sky `#88D8F2`
  - Status: success `#5CA300`, warning/hot `#FF8904`, error/E-stop `#FF6467`
  - Font **Public Sans** (Black 900 headlines, ExtraBold 800 section heads, Regular 400 body). Radius 10px, spacing unit 4px, **Bootstrap Icons**
- Logo: **`logo2.png` only** (full lockup). The star mark (`stars.svg`) is for small spaces such as the TFT rail, boot screen and favicon.
- Bambu-inspired: big, clear, friendly. One task per screen.

## 3. TFT navigation model (480 × 320)

- **Single left column (rail) of 4 page icons** plus E-stop.
- Every page fits on one screen: **no scrolling, no "more" tabs**. Only **Settings** may scroll.
- The first icon is Home.

| # | Icon | Page | Purpose |
|---|---|---|---|
| 1 | Home | **Home** | Idle: reprint last + recent prints + preheat. Printing: live job card |
| 2 | Files | **Print** | Browse/print files with thumbnails |
| 3 | Sliders | **Controls** | Temperatures, fan, filament, movement |
| 4 | Gear | **Settings** | Scrollable. Contains the Advanced mode toggle |
| — | ⛔ | **E-stop** | Pinned at the bottom, red, **always visible**. **Tap, then confirm** |

## 4. Fixed values

| Item | Value |
|---|---|
| Speed presets | **Silent 50% · Normal 100% · Fast 125% · Draft 150%** (sets speed % only, `M220`. No acceleration changes) |
| Flow | **−1% / +1% buttons**, hard limits **40%–120%** |
| PLA | Nozzle 210 °C · Bed 60 °C |
| PETG | Nozzle 240 °C · Bed 80 °C |
| TPU | Nozzle 225 °C · Bed **40 °C** |

## 5. Action inventory

Legend: **N** = Normal mode · **A** = Advanced mode only · 🔒 = locked while printing · ⚠️ = needs confirmation · Where: T = TFT, M = Mainsail

### Home: idle
| Action | Mode | Where | Notes |
|---|---|---|---|
| Reprint last job | N ⚠️ | T M | Confirm: **"Is the bed clear?"** |
| Recent prints (thumbnails), tap to reprint | N ⚠️ | T M | Same bed-clear confirmation |
| Preheat PLA / PETG / TPU | N | T M | One tap. Uses the table in section 4 |
| Cool down | N | T M | |
| Printer status (temps, state, idle-timeout countdown if heaters are on) | N | T M | |

### Home: printing
| Action | Mode | Where | Notes |
|---|---|---|---|
| Thumbnail, progress %, time left, layer x/y | N | T M | |
| Pause / Resume | N | T M | |
| Cancel print | N ⚠️ | T M | |
| **Cancel object** | N ⚠️ | T M | Shows **a bed map with each object's position** and **a list of part names**. Tap on the map or in the list, then confirm. Requires `[exclude_object]` + Orca "Label objects" |
| Speed preset buttons: Silent / Normal / Fast / Draft | N | T M | Active preset highlighted |
| Nozzle / bed target temperature | N | T M | Clamped to config `max_temp` |
| Part fan % | N | T M | |
| Flow % (−1 / +1) | N | T M | 40–120% |
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
| **Load filament**: pick material → heats to the right temp → load → purge → "Purge more / Done" | N | T M | 🔒 while printing (the runout flow handles mid-print changes) |
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
| **Advanced mode** on/off | N | T M | ❓ PIN-protected or not (Q-024) |
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
| Filament runout (sensor planned) | Auto-pause → "Filament ran out" screen → guided unload/load → Resume. The UI is built now and becomes active when the sensor is added to the config |
| Print finished | "Done" card → **Print again** (bed-clear confirm) / Dismiss |
| Error / shutdown | Full-screen red state with plain-language message + "Restart" (⚠️) |
| E-stop pressed | Confirm dialog → stop → error state above |

## 6. Printer-state rules

| State | Rules |
|---|---|
| Idle | Everything available (per mode) |
| Heating | All available. Show progress to target |
| Printing | Motion, homing, filament load/unload, shutdown **locked**. Temps/fan/flow/speed editable |
| Paused | Resume/Cancel prominent. Filament change allowed |
| Error/shutdown | Only status, Restart, E-stop. Everything else disabled |

## 7. Things the real printer config must include (Phase 3.5)

`[exclude_object]`, `[pause_resume]`, `[virtual_sdcard]`, `[display_status]`, `[idle_timeout]` (already present per user), `[filament_switch_sensor]` (when fitted), `min_extrude_temp`, `[verify_heater]` defaults left as they are.

## 8. OrcaSlicer settings to check

- **Label objects** ON and **Exclude objects** ON (needed for cancel object + the bed map)
- **Thumbnails** in a Klipper-readable format (e.g. `48x48/PNG, 300x300/PNG`)
- Start G-code passes bed/nozzle temps to `PRINT_START`

## 9. Implementation approach (decided)

- **Mainsail:** no code changes. Theme folder (`.theme/`) + layout/presets/macros.
- **KlipperScreen:** a **StarStackCo fork** with minimal, documented changes (`FORK_CHANGES.md` lists every change and how to merge upstream updates).

---

### Changes v1 → v2
- Single dark theme (no light mode)
- Logo: `logo2.png` only
- Z babystep removed
- Speed presets fixed: 50 / 100 / 125 / 150%, speed only
- Flow: ±1% buttons, 40–120% cap
- Material temps fixed, with TPU bed at 40 °C
- Cancel object shows a bed map + part-name list
- E-stop: tap, then confirm
- Idle timeout: handled by the printer config, display only
- Runout UI: build now
- KlipperScreen fork approved
