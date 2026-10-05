#!/usr/bin/env bash
# From this PC: make sure ~/klipper-ui exists on the Pi (on the chosen branch), then run install.sh there.
#   scripts/pi-install.sh [--branch dev] [install.sh options: --dry-run | --uninstall | --fix-printer-cfg]
# Default branch is main (stable). Use --branch dev to bench-test unreleased changes.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BRANCH=main
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --branch) BRANCH="$2"; shift 2 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
"$ROOT/scripts/pi.sh" "set -e
if [ ! -d ~/klipper-ui/.git ]; then git clone -q https://github.com/StarStackCo/klipper-ui.git ~/klipper-ui; fi
cd ~/klipper-ui && git fetch -q origin && git checkout -q -B $BRANCH origin/$BRANCH && git branch -q -u origin/$BRANCH
echo \"klipper-ui on \$(git rev-parse --abbrev-ref HEAD) \$(git log --oneline -1)\"
bash ~/klipper-ui/install.sh ${ARGS[*]}"
