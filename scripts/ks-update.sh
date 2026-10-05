#!/usr/bin/env bash
# Touchscreen development loop (the Pi tracks the fork):
#   1. push the fork branch (refuses if there are uncommitted changes)
#   2. Pi: check out that branch of ~/KlipperScreen and fast-forward it
#   3. restart KlipperScreen, optional screenshot
#   scripts/ks-update.sh [--branch dev|starstack] [screenshot.png]      default branch: dev
# Bench-testing dev makes Mainsail show "not on the primary branch" until you switch back:
#   scripts/ks-update.sh --branch starstack
# The theme is generated: run tools/starstack/build_theme.py in the fork and commit before this.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FORK="${KS_FORK:-$ROOT/../KlipperScreen-starstack}"
BRANCH=dev
SHOT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --branch) BRANCH="$2"; shift 2 ;;
    *) SHOT="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; shift ;;
  esac
done
cd "$FORK"
if [ -n "$(git status --porcelain)" ]; then
  echo "Fork has uncommitted changes. Commit them first:"; git status --short; exit 1
fi
if [ "$BRANCH" != starstack ]; then git push -q origin "$BRANCH"; echo "pushed $BRANCH $(git rev-parse --short "$BRANCH")"; fi
"$ROOT/scripts/pi.sh" "set -e; cd ~/KlipperScreen && git fetch -q --tags origin && git checkout -q -B $BRANCH origin/$BRANCH && git log --oneline -1 && echo \"uncommitted on Pi: \$(git status --porcelain | wc -l)\"; curl -s -X POST 'http://localhost:7125/machine/services/restart?service=KlipperScreen' >/dev/null; sleep 8; systemctl is-active KlipperScreen"
[ -n "$SHOT" ] && "$ROOT/scripts/ks-screenshot.sh" "$SHOT"
exit 0
