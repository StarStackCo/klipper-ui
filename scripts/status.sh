#!/usr/bin/env bash
# One read-only look at the Pi: Klipper state, print state, temperatures, repo branches, recent klippy errors.
#   scripts/status.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT/scripts/pi.sh" "curl -s -m 5 'http://localhost:7125/printer/objects/query?print_stats&extruder&heater_bed&webhooks' | python3 -c '
import sys, json
try:
    s = json.load(sys.stdin)[\"result\"][\"status\"]
except Exception:
    print(\"Moonraker: no reply (Klipper or Moonraker down)\"); sys.exit()
w, p = s[\"webhooks\"], s[\"print_stats\"]
print(\"Klipper:      \", w[\"state\"], \"-\", (w[\"state_message\"] or \"-\").splitlines()[0])
print(\"Print:        \", p[\"state\"], p[\"filename\"] or \"\")
for h in (\"extruder\", \"heater_bed\"):
    print(\"%-14s %5.1f / %.0f C\" % (h + \":\", s[h][\"temperature\"], s[h][\"target\"]))
'
for r in ~/klipper-ui ~/KlipperScreen ~/klipper ~/moonraker; do
  [ -d \$r/.git ] && printf '%-14s %s %s\n' \"\${r##*/}:\" \"\$(git -C \$r rev-parse --abbrev-ref HEAD)\" \"\$(git -C \$r log --oneline -1 | cut -c1-60)\"
done
e=\$(tac ~/printer_data/logs/klippy.log | sed '/^Start printer at/q' | tac | sed '/^===== Config file/,/^=======================$/d' | grep -iE 'error|!!' | tail -5)
echo 'klippy.log errors since the last start:'; echo \"\${e:-none}\" | sed 's/^/  /'"
