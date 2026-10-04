#!/usr/bin/env bash
# Drive the bench touchscreen through StarStack devtools (needs ~/.starstack_dev on the Pi).
#   scripts/ks-tap.sh "click Load filament" [screenshot.png]
#   scripts/ks-tap.sh "show ss_print" shot.png
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/pi.sh" "rm -f ~/.starstack_dev_out; echo '$1' > ~/.starstack_dev_cmd; for i in 1 2 3 4 5 6 7 8 9 10; do sleep 0.3; [ -f ~/.starstack_dev_out ] && break; done; sleep 0.6; cat ~/.starstack_dev_out 2>/dev/null || echo 'no reply (devtools off?)'"
[ -n "$2" ] && "$ROOT/scripts/ks-screenshot.sh" "$2" >/dev/null && echo "  screenshot: $2"
exit 0
