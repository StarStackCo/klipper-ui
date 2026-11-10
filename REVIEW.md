# Reviewing a change to klipper-ui

For any reviewer, human or Claude (`/code-review`, `/security-review`, a fresh-context subagent). This repo runs
a heated, moving machine in someone's home. A missed bug can start a fire, crash the toolhead, ruin a print or
brick the printer. Look for those first. Style matters least.

## What failure looks like here

| Area | It fails when it... |
|---|---|
| `macros/`, macros in `config/*/printer.cfg` | moves, heats or extrudes when it shouldn't, blocks the G-code queue during a print, or leaves G-code state changed |
| `config/` | sends a pin, limit or sensor to the wrong place, or loosens a safety limit |
| `install.sh`, `update/`, `scripts/`, `usb/`, `boot/` | leaves a printer that won't boot or update, wipes the user's config, acts while printing, or needs a password typed by Claude |
| `tools/`, `tests/` | passes something it should reject (a check that can't fail is worse than none) |
| `docs/` | says something untrue: "done" with no check behind it, a number with no source, a step the code no longer does |
| `mainsail-theme/` | hides or moves a control the user needs. Low risk otherwise |

## Always flag as Important

- A restart, firmware restart or macro reload that can run while `print_stats.state` is printing or paused.
- Any change that raises or removes `max_temp`, `min_temp`, `min_extrude_temp`, `verify_heater`, endstops,
  kinematics or `max_extrude_only_distance`. Safety limits may only get stricter (PLAN 3.1).
- A blocking heat wait (`M109`, `M190`, `TEMPERATURE_WAIT`) reachable during a print.
- A move or extrude with no temperature, homing or print-state gate where the neighbors have one.
- Moonraker `trusted_clients` narrowed to one subnet (D-102).
- A key, token, password or IP-plus-key pair in the repo.
- Pi access that bypasses `scripts/pi.sh`, or a script that asks Claude to type sudo or Wi-Fi passwords (D-007, D-008).
- A price, published spec or business claim stated as fact. Those live in the claude.ai project.
- `config/s1/` treated as the production S1 (D-102).
- A collision check that relies on the PZ probe while moving (D-099).

## Missing paperwork (Important when the code changed)

- A macro change without an update to `docs/macro-safety-review.md`.
- A behavior change without a `D-NNN` (or `D-NEW` on a branch) row in `docs/DECISIONS.md`.
- A deploy without a build/deploy log row, or a test without a Run section in `docs/test-checklist.md`.

## Already checked by CI, don't repeat

`tools/check_macros.py` (macros parse, Klipper-callable names, safety rules), `tools/check_ids.py`, JSON
validity, flake8 errors, pytest, shellcheck errors, trufflehog. Flag a gap in these checks instead.

## Skip

`docs/archive/`, `docs/data/`, `backups/`, `logs/`, `design/`, `splash/` images, `__pycache__/`.

## How to report

- Start with a count: "2 Important, 1 Nit." If nothing needs fixing, say so in one line.
- Every finding gives `file:line` and the concrete way it fails (inputs or printer state, then what goes wrong).
- Tag each finding **Important**, **Nit** or **Pre-existing** (old code the change didn't touch). At most 3 Nits.
- For a bug fix, check it fixes the root cause in the shared code, not one caller.
- When one instance of a bug class turns up, list every instance, not just the first.
- Don't repeat a finding already raised and answered.
- American spelling, no em dashes.

## Rounds

After the first two rounds, review only the new diff. After three rounds on the same change, stop and say the
approach may need rethinking. When the same finding comes up across changes, propose fixing it at the source:
a rule in `check_macros.py`, a line here, or a skill.
