#!/usr/bin/env bash
# Development loop now that the Pi tracks the fork (step 6):
#   1. commit + push the fork (refuses if there are uncommitted changes)
#   2. Pi: fetch and fast-forward ~/KlipperScreen to origin/starstack
#   3. restart KlipperScreen, optional screenshot
#   scripts/ks-update.sh [screenshot.png]
# The theme is generated: run scripts/build_ks_theme.py and commit the fork before this.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FORK="${KS_FORK:-$ROOT/../KlipperScreen-starstack}"
SHOT=""
[ -n "$1" ] && SHOT="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
cd "$FORK"
if [ -n "$(git status --porcelain)" ]; then
  echo "Fork has uncommitted changes. Commit them first:"; git status --short; exit 1
fi
git push -q origin starstack
echo "pushed $(git rev-parse --short HEAD)"
"$ROOT/scripts/pi.sh" 'set -e; cd ~/KlipperScreen && git fetch -q --tags origin && git merge -q --ff-only origin/starstack && git log --oneline -1 && echo "uncommitted on Pi: $(git status --porcelain | wc -l)"; curl -s -X POST "http://localhost:7125/machine/services/restart?service=KlipperScreen" >/dev/null; sleep 8; systemctl is-active KlipperScreen'
[ -n "$SHOT" ] && "$ROOT/scripts/ks-screenshot.sh" "$SHOT"
exit 0
