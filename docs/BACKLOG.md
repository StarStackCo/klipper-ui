# Backlog

Things to do later. Each item gets a decision/progress entry in DECISIONS.md when it's started.

| # | Added | Item | Notes |
|---|---|---|---|
| B-1 | 2026-10-05 | **Restyle the on-screen keyboard** (Wi-Fi password, console/command line, any text input) to match the StarStack UI | Dark surfaces, Public Sans, 10px corners. Keys ≥ 44 px tall, ≥ 14–16 px from the screen edges, no tiny keys. Must not cover the STOP rail. KlipperScreen keyboard: `ks_includes/widgets/keyboard.py` (and matchbox option) |
| B-2 | 2026-10-05 | Review and merge the waiting **upstream KlipperScreen update** (v0.4.6-26 → v0.4.6-64) | The sync workflow found it (branch `upstream-sync`). Bench-test from `dev` first |
| B-3 | 2026-10-05 | Phase 3.5: real `printer.cfg`, safety review, board firmware update, staged power-up on the full printer | Needs wiring details from the user |
| B-4 | 2026-10-05 | Mainsail macro panels order (Speed, Preheat, Filament, Advanced) | Q-042 |
| B-5 | 2026-10-05 | Turn off bench devtools (`rm ~/.starstack_dev`) before the full-printer phase | |
