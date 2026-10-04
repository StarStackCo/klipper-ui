#!/usr/bin/env bash
# Apply (or roll back) the Mainsail UI settings in mainsail-theme/settings.json
# via Moonraker's database API on the Pi (localhost:7125, no restart needed).
#   scripts/mainsail-settings.sh             apply "value"
#   scripts/mainsail-settings.sh --rollback  apply "was" (Mainsail defaults)
#   scripts/mainsail-settings.sh --show      print current values only
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIELD=value; [ "$1" = "--rollback" ] && FIELD=was
python - "$ROOT/mainsail-theme/settings.json" "$FIELD" "${1:-}" > "$ROOT/logs/.mainsail-settings.cmd" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1], encoding='utf-8'))['settings']
field, mode = sys.argv[2], sys.argv[3]
lines = []
for s in cfg:
    k = s['key']
    if mode != '--show':
        body = json.dumps({"namespace": "mainsail", "key": k, "value": s[field]})
        lines.append("curl -s -X POST http://localhost:7125/server/database/item -H 'Content-Type: application/json' -d '%s' >/dev/null" % body)
    lines.append("printf '%-34s ' '" + k + "'; curl -s 'http://localhost:7125/server/database/item?namespace=mainsail&key=" + k + "' | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"result\",{}).get(\"value\",\"(not set: Mainsail default)\"))' 2>/dev/null || echo '(not set: Mainsail default)'")
print('; '.join(lines))
PY
"$ROOT/scripts/pi.sh" "$(cat "$ROOT/logs/.mainsail-settings.cmd")"
echo "Reload Mainsail (Ctrl+Shift+R) to see changes."
