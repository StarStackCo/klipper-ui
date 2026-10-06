#!/usr/bin/env bash
# StarStack printer UI installer. Run ON THE PRINTER'S PI (as the normal user, not root):
#
#   git clone https://github.com/StarStackCo/klipper-ui.git ~/klipper-ui
#   bash ~/klipper-ui/install.sh                 install / update everything (safe to re-run)
#   bash ~/klipper-ui/install.sh --dry-run       show what would change, change nothing
#   bash ~/klipper-ui/install.sh --uninstall     back to stock Mainsail + KlipperScreen
#   bash ~/klipper-ui/install.sh --fix-printer-cfg   also add the required lines to printer.cfg
#
# What it does (each step prints what it changed; backups are made once, never overwritten):
#   1. Links the StarStack macros and Mainsail theme from this repo into ~/printer_data/config
#      (so Mainsail's update manager updates them with one click)
#   2. Checks printer.cfg has what the UI needs (and adds it with --fix-printer-cfg)
#   3. Adds [update_manager klipper-ui] and points [update_manager KlipperScreen] at the StarStack fork
#   4. Switches ~/KlipperScreen to the StarStack fork (re-clones if the git folder is damaged),
#      installs the Public Sans font and selects the starstack theme
#   5. Applies Mainsail UI settings + macro groups + dashboard panel order (Moonraker database)
#   6. Restarts Moonraker, Klipper and KlipperScreen
# It refuses to run while a print is in progress.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="${PRINTER_CONFIG:-$HOME/printer_data/config}"
MOON="http://localhost:7125"
KS_DIR="$HOME/KlipperScreen"
KS_FORK="https://github.com/StarStackCo/KlipperScreen-starstack.git"
KS_UP="https://github.com/KlipperScreen/KlipperScreen.git"
UI_ORIGIN="https://github.com/StarStackCo/klipper-ui.git"
DRY=0; MODE=install; FIX_CFG=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --uninstall) MODE=uninstall ;;
    --fix-printer-cfg) FIX_CFG=1 ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) echo "unknown option: $a"; exit 2 ;;
  esac
done

say() { printf '\033[1;36m==\033[0m %s\n' "$*"; }
do_() { if [ "$DRY" = 1 ]; then echo "   (dry-run) $*"; else eval "$@"; fi; }
backup_once() { [ -e "$1" ] && [ ! -e "$1.pre-starstack" ] && do_ "cp -a '$1' '$1.pre-starstack'" && echo "   backup: $1.pre-starstack" || true; }

[ "$(id -u)" != 0 ] || { echo "Run as the normal printer user, not root."; exit 1; }
[ -d "$CFG" ] || { echo "Config folder not found: $CFG"; exit 1; }
STATE=$(curl -s -m 5 "$MOON/printer/objects/query?print_stats" | python3 -c 'import sys,json;print(json.load(sys.stdin)["result"]["status"]["print_stats"]["state"])' 2>/dev/null || echo unknown)
if [ "$STATE" = printing ] || [ "$STATE" = paused ]; then echo "A print is $STATE. Run this when the printer is idle."; exit 1; fi

link() {  # link <repo path> <config path>
  local src="$REPO/$1" dst="$CFG/$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then echo "   ok: $2 -> klipper-ui/$1"; return; fi
  backup_once "$dst"
  do_ "rm -rf '$dst' && ln -s '$src' '$dst'"; echo "   linked: $2 -> klipper-ui/$1"
}

unlink_restore() {
  local dst="$CFG/$1"
  if [ -L "$dst" ]; then do_ "rm '$dst'"; fi
  if [ -e "$dst.pre-starstack" ]; then do_ "mv '$dst.pre-starstack' '$dst'"; echo "   restored $1"; fi
}

moonraker_sections() {
  backup_once "$CFG/moonraker.conf"
  [ "$DRY" = 1 ] && { echo "   (dry-run) update [update_manager klipper-ui] and [update_manager KlipperScreen]"; return; }
  python3 - "$CFG/moonraker.conf" "$REPO" "$UI_ORIGIN" "$KS_FORK" <<'PY'
import re, sys
p, repo, ui_origin, ks_fork = sys.argv[1:]
s = open(p).read()
def section(name):
    return re.search(r'^\[%s\]\n(.*?)(?=^\[|\Z)' % re.escape(name), s, re.S | re.M)
ui = ('[update_manager klipper-ui]\n'
      '# STARSTACK-ADDED: StarStack macros + Mainsail theme (klipper-ui install.sh)\n'
      'type: git_repo\npath: %s\norigin: %s\nprimary_branch: main\nmanaged_services: klipper\n\n' % (repo, ui_origin))
m = section('update_manager klipper-ui')
s = s[:m.start()] + ui + s[m.end():] if m else s.rstrip('\n') + '\n\n' + ui
m = section('update_manager KlipperScreen')
if m:
    body = re.sub(r'^(origin|primary_branch):.*\n|^# STARSTACK.*\n', '', m.group(1), flags=re.M)
    body = ('# STARSTACK-ADDED: track the public StarStack fork (klipper-ui install.sh)\n'
            'origin: %s\nprimary_branch: starstack\n' % ks_fork) + body
    s = s[:m.start(1)] + body + s[m.end(1):]
open(p, 'w').write(s)
print('   moonraker.conf: [update_manager klipper-ui] + KlipperScreen -> StarStack fork')
PY
}

printer_cfg_check() {
  local pc="$CFG/printer.cfg" missing=()
  grep -q '^\[include starstack_macros.cfg\]' "$pc" || missing+=("[include starstack_macros.cfg]")
  grep -q '^\[save_variables\]' "$pc" || missing+=("[save_variables]")
  grep -q '^\[exclude_object\]' "$pc" || missing+=("[exclude_object]")
  grep -q '^\[include mainsail.cfg\]' "$pc" || missing+=("[include mainsail.cfg]")
  if [ ${#missing[@]} = 0 ]; then echo "   ok: printer.cfg has everything the UI needs"; return; fi
  echo "   printer.cfg is missing: ${missing[*]}"
  if [ "$FIX_CFG" = 1 ]; then
    backup_once "$pc"
    local block="\n# STARSTACK-ADDED: required by the StarStack UI (klipper-ui install.sh)\n"
    for m in "${missing[@]}"; do
      case "$m" in
        "[save_variables]") block+="[save_variables]\nfilename: ~/printer_data/config/variables.cfg\n" ;;
        *) block+="$m\n" ;;
      esac
    done
    do_ "printf '$block' >> '$pc'"; echo "   added to printer.cfg"
    [ -e "$CFG/variables.cfg" ] || do_ "printf '[Variables]\nloaded_material = \x27NONE\x27\n' > '$CFG/variables.cfg'"
  else
    echo "   -> add them by hand, or re-run with --fix-printer-cfg"
  fi
}

klipperscreen_fork() {
  if [ ! -d "$KS_DIR" ]; then echo "   KlipperScreen not installed: install it with KIAUH first, then re-run"; return; fi
  if ! git -C "$KS_DIR" fsck --no-dangling >/dev/null 2>&1; then
    local b="$KS_DIR.corrupt-$(date +%Y%m%d-%H%M)"
    echo "   KlipperScreen git folder is damaged: keeping it as $b and re-cloning"
    do_ "mv '$KS_DIR' '$b' && git clone -q -b starstack '$KS_FORK' '$KS_DIR'"
  fi
  do_ "git -C '$KS_DIR' remote set-url origin '$KS_FORK'"
  git -C "$KS_DIR" remote get-url upstream >/dev/null 2>&1 || do_ "git -C '$KS_DIR' remote add upstream '$KS_UP'"
  do_ "git -C '$KS_DIR' remote set-url --push upstream DISABLED"
  do_ "git -C '$KS_DIR' fetch -q --tags origin && git -C '$KS_DIR' checkout -q -f -B starstack origin/starstack && git -C '$KS_DIR' branch -q -u origin/starstack"
  [ "$DRY" = 1 ] || echo "   KlipperScreen: $(git -C "$KS_DIR" describe --tags --always) on starstack"
  do_ "mkdir -p ~/.local/share/fonts && cp '$KS_DIR'/styles/starstack/fonts/*.ttf ~/.local/share/fonts/ && fc-cache -f ~/.local/share/fonts"
  local kc="$CFG/KlipperScreen.conf"
  [ -e "$kc" ] || do_ "touch '$kc'"
  if ! grep -q '^theme: starstack' "$kc" 2>/dev/null; then
    backup_once "$kc"
    do_ "printf '# STARSTACK-ADDED: StarStack theme (klipper-ui install.sh)\n[main]\ntheme: starstack\n\n' | cat - '$kc' > '$kc.tmp' && mv '$kc.tmp' '$kc'"
  fi
  echo "   theme: starstack, fonts installed"
}

restart_all() {
  [ "$DRY" = 1 ] && { echo "   (dry-run) restart moonraker, klipper, KlipperScreen"; return; }
  curl -s -X POST "$MOON/machine/services/restart?service=moonraker" >/dev/null || true; sleep 8
  curl -s -X POST "$MOON/printer/restart" >/dev/null || true; sleep 6
  curl -s -X POST "$MOON/machine/services/restart?service=KlipperScreen" >/dev/null || true; sleep 4
  echo "   klipper: $(curl -s -m 5 $MOON/printer/info | python3 -c 'import sys,json;print(json.load(sys.stdin)["result"]["state"])' 2>/dev/null || echo '?')"
}

if [ "$MODE" = uninstall ]; then
  say "Uninstall StarStack UI"
  unlink_restore starstack_macros.cfg
  unlink_restore .theme
  for f in moonraker.conf KlipperScreen.conf; do
    [ -e "$CFG/$f.pre-starstack" ] && do_ "cp '$CFG/$f.pre-starstack' '$CFG/$f'" && echo "   restored $f"
  done
  if [ -d "$KS_DIR" ]; then
    do_ "git -C '$KS_DIR' remote set-url origin '$KS_UP' && git -C '$KS_DIR' fetch -q origin && git -C '$KS_DIR' checkout -q -f -B master origin/master"
  fi
  [ "$DRY" = 1 ] || python3 "$REPO/tools/apply_mainsail.py" --rollback
  echo "   printer.cfg was not changed: remove the StarStack lines by hand if you added them"
  restart_all
  exit 0
fi

say "1/6 Link StarStack macros + Mainsail theme"
link macros/starstack_macros.cfg starstack_macros.cfg
link mainsail-theme/.theme .theme
say "2/6 Check printer.cfg"
printer_cfg_check
say "3/6 Moonraker update manager"
moonraker_sections
say "4/6 KlipperScreen -> StarStack fork"
klipperscreen_fork
say "5/6 Mainsail settings + macro groups + panel order"
if [ "$DRY" = 1 ]; then echo "   (dry-run) apply mainsail-theme/settings.json + macrogroups.json + dashboard.json"; else python3 "$REPO/tools/apply_mainsail.py" | sed 's/^/   /'; fi
say "6/6 Restart services"
restart_all
say "Done. Updates now appear in Mainsail: Machine > Update Manager (klipper-ui, KlipperScreen)."
