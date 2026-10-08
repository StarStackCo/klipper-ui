#!/usr/bin/env bash
# Pin the Klipper and Moonraker versions installed on the test printer as the tested versions
# (update/versions.conf, klipper-ui D-087). Run after they passed the checklist on the S1.
#   scripts/pin-versions.sh            write the pins (then commit and release)
#   scripts/pin-versions.sh --latest   first move the S1 to the newest Klipper and Moonraker to try
#                                      them (the update helper then updates the board firmware)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PI="$ROOT/scripts/pi.sh"
F="$ROOT/update/versions.conf"
if [ "${1:-}" = --latest ]; then
  "$PI" 'for r in klipper moonraker; do git -C ~/$r fetch -q origin && git -C ~/$r merge -q --ff-only "origin/$(git -C ~/$r rev-parse --abbrev-ref HEAD)" && echo "$r: $(git -C ~/$r describe --tags)"; done
         curl -s -X POST "localhost:7125/machine/services/restart?service=moonraker" >/dev/null; sleep 10
         curl -s -X POST localhost:7125/printer/restart >/dev/null; echo "restarted: now test, then run pin-versions.sh"'
  exit 0
fi
info=$("$PI" 'for r in klipper moonraker; do echo "$r $(git -C ~/$r rev-parse HEAD) $(git -C ~/$r describe --tags)"; done')
today=$(date +%F)
py=$(command -v py || command -v python3)  # py first: on Windows "python3" can be a Store shortcut
"$py" - "$F" "$today" <<PY
import re, sys
path, today = sys.argv[1:]
text = open(path, encoding="utf-8").read()
for line in """$info""".strip().splitlines():
    app, sha, desc = line.split()
    text, n = re.subn(r"(\[update_manager %s\]\n)# .*\npinned_commit: \w+" % app,
                      r"\g<1># %s (S1, %s)\npinned_commit: %s" % (desc, today, sha), text)
    assert n == 1, app
    print("%s: %s" % (app, desc))
open(path, "w", encoding="utf-8", newline="\n").write(text)
PY
echo "Pinned in update/versions.conf: commit, then scripts/release.sh"
