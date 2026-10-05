#!/usr/bin/env bash
# Step 6: make the Pi's KlipperScreen track the public StarStack fork, so Mainsail's
# update manager shows and installs StarStack updates. Safe to run more than once.
#   scripts/install-ks-fork.sh             install / re-sync
#   scripts/install-ks-fork.sh --rollback  back to official KlipperScreen (stock UI) + original moonraker.conf
#
# What it changes on the Pi:
#   ~/KlipperScreen            origin → StarStackCo/KlipperScreen-starstack, branch starstack (upstream kept as remote)
#                              a damaged repo (power cut) is moved aside and re-cloned
#   moonraker.conf             [update_manager KlipperScreen] origin + primary_branch (backup: moonraker.conf.pre-ks-fork)
#   ~/.local/share/fonts       Public Sans (the theme's font)
#   KlipperScreen.conf         theme: starstack (only if missing)
# Every step stops the script if it fails, so a failed step never leaves later steps half-applied.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PI="$ROOT/scripts/pi.sh"
FORK_URL="https://github.com/StarStackCo/KlipperScreen-starstack.git"
UP_URL="https://github.com/KlipperScreen/KlipperScreen.git"
CONF='~/printer_data/config/moonraker.conf'

if [ "$1" = "--rollback" ]; then
  "$PI" "set -e; cd ~/KlipperScreen && git remote set-url origin $UP_URL && git fetch -q origin && git checkout -q -f -B master origin/master && git branch -vv | head -1; \
         if [ -f $CONF.pre-ks-fork ]; then cp $CONF.pre-ks-fork $CONF && echo 'moonraker.conf restored'; fi; \
         sed -i '/^# STARSTACK-ADDED: StarStack theme/,+2d' ~/printer_data/config/KlipperScreen.conf; echo 'theme line removed'"
  "$PI" 'curl -s -X POST "http://localhost:7125/machine/services/restart?service=moonraker" >/dev/null; sleep 6; curl -s -X POST "http://localhost:7125/machine/services/restart?service=KlipperScreen"; echo'
  exit 0
fi

echo "== 1. KlipperScreen folder -> StarStack fork"
"$PI" "set -e
rm -f ~/.starstack-ks-deployed.txt ~/.ssh/ks_starstack_deploy ~/.ssh/ks_starstack_deploy.pub
cd ~
if ! git -C KlipperScreen fsck --no-dangling >/dev/null 2>&1; then
  B=KlipperScreen.corrupt-\$(date +%Y%m%d-%H%M); mv KlipperScreen \$B
  echo \"damaged repo kept as ~/\$B, re-cloning\"
  git clone -q -b starstack $FORK_URL KlipperScreen
fi
cd KlipperScreen
git remote set-url origin $FORK_URL
git remote get-url upstream >/dev/null 2>&1 || git remote add upstream $UP_URL
git remote set-url --push upstream DISABLED
git fetch -q --tags origin
git checkout -q -f -B starstack origin/starstack
git branch -q -u origin/starstack
git branch -vv | head -1
echo \"uncommitted files: \$(git status --porcelain | wc -l)\"" || { echo "STEP 1 FAILED: nothing else was changed"; exit 1; }

echo "== 2. moonraker.conf update_manager"
"$PI" "set -e; [ -f $CONF.pre-ks-fork ] || cp $CONF $CONF.pre-ks-fork; python3 - $CONF <<'PY'
import re, sys, os
p = os.path.expanduser(sys.argv[1]); s = open(p).read()
m = re.search(r'^\[update_manager KlipperScreen\]\n(.*?)(?=^\[|\Z)', s, re.S | re.M)
body = m.group(1)
body = re.sub(r'^origin:.*\n', '', body, flags=re.M)
body = re.sub(r'^primary_branch:.*\n', '', body, flags=re.M)
body = re.sub(r'^# STARSTACK.*\n', '', body, flags=re.M)
body = ('# STARSTACK-ADDED: track the public StarStack fork (klipper-ui scripts/install-ks-fork.sh)\n'
        'origin: $FORK_URL\nprimary_branch: starstack\n') + body
s = s[:m.start(1)] + body + s[m.end(1):]
open(p, 'w').write(s)
print(open(p).read()[m.start():m.start() + 420])
PY" || { echo "STEP 2 FAILED"; exit 1; }

echo "== 3. fonts + theme"
"$PI" 'set -e; mkdir -p ~/.local/share/fonts && cp ~/KlipperScreen/styles/starstack/fonts/*.ttf ~/.local/share/fonts/ && fc-cache -f ~/.local/share/fonts; C=~/printer_data/config/KlipperScreen.conf; grep -q "^theme: starstack" $C || { printf "# STARSTACK-ADDED: StarStack theme (klipper-ui repo)\n[main]\ntheme: starstack\n\n" | cat - $C > $C.tmp && mv $C.tmp $C; }; echo "fonts: $(fc-list | grep -c "Public Sans")"'

echo "== 4. restart Moonraker, refresh update status, restart KlipperScreen"
"$PI" 'curl -s -X POST "http://localhost:7125/machine/services/restart?service=moonraker" >/dev/null; sleep 10; curl -s -X POST "http://localhost:7125/machine/update/refresh?name=KlipperScreen" | python3 -c "import sys,json;k=json.load(sys.stdin)[\"result\"][\"version_info\"][\"KlipperScreen\"];print({x:k.get(x) for x in (\"remote_url\",\"branch\",\"version\",\"is_valid\",\"is_dirty\",\"corrupt\",\"warnings\",\"anomalies\")})"; curl -s -X POST "http://localhost:7125/machine/services/restart?service=KlipperScreen" >/dev/null; sleep 8; systemctl is-active KlipperScreen'
