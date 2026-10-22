---
name: release
description: Release dev to stable for klipper-ui and the KlipperScreen fork with scripts/release.sh, then confirm the S1 updates cleanly. Use when asked to release, ship, publish a version, tag vX.Y.Z, merge dev into main or starstack, or pin tested Klipper/Moonraker versions.
---

# Releasing dev to stable (both repos)

Printers install klipper-ui `main` and the fork's `starstack` through Moonraker's update manager, so a
release reaches every printer on its next "Update everything". The script is `scripts/release.sh`; README
"Update" describes it.

## Procedure
1. **Get the user's OK** for the release and the version number (D-003).
2. **Checklist first.** Everything going out has a passing Run in `docs/test-checklist.md` on the S1. Items
   still marked 🟡 in DECISIONS.md are not released.
3. **Tested versions.** If Klipper or Moonraker should move: `scripts/pin-versions.sh --latest`, run the
   checklist, then `scripts/pin-versions.sh` and commit `update/versions.conf` on `dev`.
4. **Both repos clean, on `dev`, pushed.** The script refuses otherwise. Check the fork too: its local `dev`
   can hold commits that only went to `bench`.
5. **Run** `scripts/release.sh vX.Y.Z "what changed"` from klipper-ui. For each repo with new commits it
   opens the PR, waits for CI, merges, levels `dev` with stable, then tags klipper-ui `main`.
6. **Log it**: a build/deploy log row in `docs/DECISIONS.md` (PR numbers, tag, stable commits).
7. **Put the S1 on the release** with the user: Update everything (touchscreen or Mainsail), then watch the
   update helper's check (`journalctl -u starstack-update` via `scripts/pi.sh`) until it records the update
   as good, and confirm the Update Manager shows every repo valid and clean.

## Gotchas
- **Only klipper-ui gets the StarStack tag.** The fork already carries upstream KlipperScreen's v0.x tags; the
  tag message records the fork commit (D-091). The first run stopped on "v0.2.0 already exists".
- **Versions stay 0.x until the first unit ships**; v1 needs `FIRST_UNIT_SHIPPED=1` (D-088).
- **Release the two repos together when they depend on each other.** A touchscreen build older than the
  klipper-ui it expects left the boot bar painting over the UI (D-072). Same for screen code that calls new
  macro parameters (D-097 `HEAT=1`).
- **Root-installed parts only change when the user runs `install.sh` with sudo** (update helper, USB import,
  boot screen). A release alone doesn't reach them; tell the user (B-14).
- **Watch the health check on the S1 after updating.** It once marked an update good before the services had
  restarted; it now needs one steady minute (D-092, v0.3.1). A failed check undoes the update by itself
  after five minutes.
- **The Update Manager flags leftovers.** An old Moonraker component link showed as untracked source files
  until removed (D-093); check for warnings after each release.
- **CI must pass on the PR**; fix on `dev` and re-run the script, the PR stays open.
