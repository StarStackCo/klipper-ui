# Backlog

Things to do later. Each item gets a decision/progress entry in DECISIONS.md when it's started.

| # | Added | Item | Notes |
|---|---|---|---|
| B-1 | 2026-10-05 | ✅ **Done 2026-10-05 (D-056)** · **Restyle the on-screen keyboard** (Wi-Fi password, console/command line, any text input) to match the StarStack UI | Dark surfaces, Public Sans, 10px corners. Keys ≥ 44 px tall, ≥ 14–16 px from the screen edges, no tiny keys. Must not cover the STOP rail. KlipperScreen keyboard: `ks_includes/widgets/keyboard.py` (and matchbox option) |
| B-2 | 2026-10-05 | ✅ **Done 2026-10-05 (D-060)** · Review and merge the waiting **upstream KlipperScreen update** (now v0.4.7-196) | The sync workflow found it (branch `upstream-sync`). Bench-test from `dev` first |
| B-3 | 2026-10-05 | Phase 3.5: real `printer.cfg`, safety review, board firmware update, staged power-up on the full printer | ✅ Done 2026-10-08 (D-081..D-084), first print OK |
| B-4 | 2026-10-05 | ✅ **Done 2026-10-05 (D-062)** · Mainsail macro panels order (Speed, Preheat, Filament, Advanced) | Q-042 |
| B-5 | 2026-10-05 | Turn off bench devtools (`rm ~/.starstack_dev`) before the full-printer phase | ✅ Done 2026-10-08 (D-084) |
| B-6 | 2026-10-05 | ✅ **Released 2026-10-06 (D-063)**, joining a real network still to try on the full printer (antenna) · Restyle the **Wi-Fi page** (stock KlipperScreen network panel) to match the StarStack UI | Bench Pi's Wi-Fi radio is off (wired Ethernet), so the stock page shows "Scanning not allowed while unavailable". Test where Wi-Fi is enabled. Still opens fine on upstream v0.4.7 (Run 5) |
| B-7 | 2026-10-05 | ✅ **Done 2026-10-05 (D-059)** · Stop KlipperScreen's **Dependabot** PRs on the fork (5 open, aimed at upstream's own dependencies) | Close them and disable version updates (see D-058) |
| B-8 | 2026-10-06 | **Starter prints** (Benchy + a few others) preloaded into `~/printer_data/gcodes/Starter prints/` by `install.sh` | **Last task** (user). Files from the user. Home shows them as "Get started" (D-066) |
| B-9 | 2026-10-06 | **Camera switch** in Advanced (Q-049a, D-078), **when a camera is fitted**: turns the webcam streamer (crowsnest, switched off by install.sh step 8 because no camera is connected) back on and enables the camera view. Needs root to enable a service at boot: do it through a small root helper like the USB import, not by loosening sudo | Open: waiting for a camera |
