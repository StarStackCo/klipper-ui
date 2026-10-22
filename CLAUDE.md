# klipper-ui: StarStack S1 printer software

Klipper, Moonraker and Mainsail setup for the StarStack S1: printer config (`config/s1/`), the macros behind
every button (`macros/`), the Mainsail theme, `install.sh`, the update helper and the PC scripts that drive
the printer's Pi. Not here: the touchscreen code (`StarStackCo/KlipperScreen-starstack`, its own CLAUDE.md),
the PZ probe board (toolboard-pz-probe), and business facts. Prices, published specs and claims live in a
claude.ai project this repo can't see: never state one, say it needs checking there.

## Read first
Read `docs/DECISIONS.md` (decisions, questions, build/deploy log; older ones in `docs/archive/`) and
`docs/PLAN.md` before changing anything. Also source of truth: `docs/test-checklist.md`,
`docs/macro-safety-review.md`, `docs/requirements.md`, `docs/BACKLOG.md`, `README.md` (install, update,
release, scripts).

## Workflow (from the docs)
- Work on `dev`. `main` is what printers install; it changes only by a PR from `dev` after the bench
  checklist passes (README). Debug builds go on branch `bench`, never `dev` (D-061).
- Nothing is deployed to the printer or pushed without the user's OK for that step (D-003). Stop and ask
  when anything is unclear (PLAN section 7). Least invasive layer first: theme, then macros, then code (PLAN 3).
- Macro changes: `python tools/check_macros.py` (CI runs it too) and an update to the macro safety review.
- Reach the Pi only through `scripts/pi.sh` (logs to `logs/`) and show every command and reply in chat.
  Claude never handles passwords, keys or tokens; the user types sudo and Wi-Fi passwords (D-007, D-008).
- Skills: `printer-config` (any config, macro or tuning change), `release` (dev to stable).

## Recording work
- A decision is a `D-NNN` row at the top of the Decisions table in DECISIONS.md, same columns; questions are
  `Q-NNN` rows; later work is a `B-NN` row in BACKLOG.md.
- Every deploy gets a build/deploy log row; every test gets a new Run section in test-checklist.md.

## Hazards and open defects
- Never restart Klipper or reload macros while printing: it ends the print. Check `print_stats.state` first.
- Shut the Pi down before unplugging it; a hard power loss corrupted a repo on the Pi (Q-045, D-035).
- `config/s1/` is the old prototype, not the production S1 (D-102).
- Moonraker `trusted_clients` must list every private range, never one subnet (D-102).
- Mainsail isn't pinned (B-12) and anyone on the network can control the printer (B-13).
- The S1 bed mesh shows the right side about 1.6 mm low; tram later (test-checklist Run 9).
- The PZ probe triggers from vibration while moving, so it can't detect collisions (D-099).
- Power loss recovery and crash detection are design only (D-098, D-099, `docs/power-loss-recovery.md`).

## Style
American spelling (D-039). Direct, and say why. No em dashes or dash-style hyphens. Point to docs instead
of repeating them; anything long belongs in a doc or a skill.
