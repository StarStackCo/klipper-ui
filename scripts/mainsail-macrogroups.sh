#!/usr/bin/env bash
# Apply / show / roll back the Mainsail macro groups in mainsail-theme/macrogroups.json
#   scripts/mainsail-macrogroups.sh             apply (mode=expert + groups)
#   scripts/mainsail-macrogroups.sh --show      print what is stored now
#   scripts/mainsail-macrogroups.sh --rollback  delete our groups, mode=simple
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-apply}"
# Build a small Python program that runs ON THE PI against Moonraker (localhost)
python - "$ROOT/mainsail-theme/macrogroups.json" "$MODE" > "$ROOT/logs/.macrogroups.py" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1], encoding='utf-8')); mode = sys.argv[2]
groups = []
for g in cfg['groups']:
    macros = []
    for i, m in enumerate(g['macros']):
        m = {'name': m} if isinstance(m, str) else m
        macros.append({'pos': i + 1, 'name': m['name'], 'color': m.get('color', 'group'),
                       'showInStandby': g['showInStandby'], 'showInPrinting': g['showInPrinting'], 'showInPause': g['showInPause']})
    groups.append({'id': g['id'], 'name': g['name'], 'color': g['color'], 'showInStandby': g['showInStandby'],
                   'showInPrinting': g['showInPrinting'], 'showInPause': g['showInPause'], 'macros': macros})
print('import json, urllib.request')
print('API = "http://localhost:7125/server/database/item"')
print('def post(k, v):\n    r = urllib.request.Request(API, data=json.dumps({"namespace": "mainsail", "key": k, "value": v}).encode(), method="POST", headers={"Content-Type": "application/json"}); urllib.request.urlopen(r).read(); print("  set", k)')
print('def delete(k):\n    try:\n        urllib.request.urlopen(urllib.request.Request(API + "?namespace=mainsail&key=" + k, method="DELETE")).read(); print("  deleted", k)\n    except Exception as e:\n        print("  (not present)", k)')
print('def show():\n    try:\n        v = json.load(urllib.request.urlopen(API + "?namespace=mainsail&key=macros"))["result"]["value"]\n    except Exception:\n        v = None\n    if not v:\n        print("  macros: (not set: Mainsail default, simple mode)"); return\n    print("  mode:", v.get("mode"))\n    for g in (v.get("macrogroups") or {}).values():\n        print("  group %-9s show[standby=%s printing=%s pause=%s]: %s" % (g["name"], g["showInStandby"], g["showInPrinting"], g["showInPause"], ", ".join(m["name"] for m in g.get("macros", []))))')
if mode == '--show':
    print('show()')
elif mode == '--rollback':
    for g in groups:
        print('delete(%r)' % ('macros.macrogroups.' + g['id']))
    print('post("macros.mode", "simple")\nshow()')
else:
    print('print("BEFORE:"); show()')
    print('post("macros.mode", %r)' % cfg['mode'])
    for g in groups:
        print('post(%r, json.loads(%r))' % ('macros.macrogroups.' + g['id'], json.dumps(g)))
    print('print("AFTER:"); show()')
PY
"$ROOT/scripts/pi.sh" 'python3 -' < "$ROOT/logs/.macrogroups.py"
[ "$MODE" = "--show" ] || echo "Reload Mainsail (Ctrl+Shift+R) to see the groups."
