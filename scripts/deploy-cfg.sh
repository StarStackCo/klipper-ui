#!/usr/bin/env bash
# Deploy printer.cfg and/or the installer (macros, theme) to the Pi the way
# .claude/skills/printer-config/deploy-to-pi.md says, then check Klipper and print a deploy log row.
#   scripts/deploy-cfg.sh D-NNN [--cfg [file]] [--install [--branch dev]] [--dry-run]
#   --cfg      copy config/s1/printer.cfg (or the given file) over the Pi's printer.cfg, keeping the Pi's
#              SAVE_CONFIG block; the old file is kept as printer.cfg.pre-dnnn
#   --install  scripts/pi-install.sh --branch <branch> (macros, theme; install.sh restarts everything)
#   --dry-run  show the Pi commands without running them
# Refuses while a print is printing or paused (a restart ends the print). Every Pi command goes through pi.sh.
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PI="$ROOT/scripts/pi.sh"
MOON=http://localhost:7125
ID="" CFG="" INSTALL=0 BRANCH=dev DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    D-[0-9]*) ID="$1"; shift ;;
    --cfg) if [ -n "$2" ] && [ "${2#--}" = "$2" ] && [ "${2#D-}" = "$2" ]; then CFG="$2"; shift 2
           else CFG="$ROOT/config/s1/printer.cfg"; shift; fi ;;
    --install) INSTALL=1; shift ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) echo "unknown option: $1"; exit 2 ;;
  esac
done
[ -n "$ID" ] || { echo "usage: $0 D-NNN [--cfg [file]] [--install [--branch dev]] [--dry-run]"; exit 2; }
[ -n "$CFG" ] || [ $INSTALL = 1 ] || { echo "nothing to deploy: give --cfg and/or --install"; exit 2; }
[ -z "$CFG" ] || [ -f "$CFG" ] || { echo "no such file: $CFG"; exit 2; }
BAK="printer.cfg.pre-$(echo "$ID" | tr 'A-Z' 'a-z')"

pi() { if [ $DRY = 1 ]; then echo "(dry-run) pi.sh: $1"; else "$PI" "$1"; fi; }

echo "== 1. Printer must be idle"
STATE=$("$PI" "curl -s -m 5 '$MOON/printer/objects/query?print_stats' | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"result\"][\"status\"][\"print_stats\"][\"state\"])' 2>/dev/null || echo unknown")
echo "   print_stats.state: $STATE"
if [ "$STATE" = printing ] || [ "$STATE" = paused ]; then echo "A print is $STATE. Deploy when it ends."; exit 1; fi

if [ -n "$CFG" ]; then
  echo "== 2. printer.cfg from ${CFG#"$ROOT"/} (backup ~/printer_data/config/$BAK)"
  if [ $DRY = 1 ]; then echo "(dry-run) upload $(sha256sum "$CFG" | cut -c1-12), keep SAVE_CONFIG block"
  else
    # Repo file without any SAVE_CONFIG block, then the Pi's own block (probe offsets, mesh) appended.
    sed '/^#\*# <---- SAVE_CONFIG ---->/,$d' "$CFG" | "$PI" "cat > /tmp/printer.cfg.new && cd ~/printer_data/config &&
      { [ -e $BAK ] && echo '   backup $BAK already exists, kept' || cp -p printer.cfg $BAK; } &&
      sed -n '/^#\*# <---- SAVE_CONFIG ---->/,\$p' printer.cfg >> /tmp/printer.cfg.new &&
      cp /tmp/printer.cfg.new printer.cfg && rm /tmp/printer.cfg.new &&
      echo \"   installed, \$(grep -c '^#\*#' printer.cfg) SAVE_CONFIG lines kept\""
  fi
fi

if [ $INSTALL = 1 ]; then
  echo "== 3. Installer on $BRANCH"
  if [ $DRY = 1 ]; then echo "(dry-run) scripts/pi-install.sh --branch $BRANCH"; else "$ROOT/scripts/pi-install.sh" --branch "$BRANCH"; fi
else
  echo "== 3. Firmware restart"
  pi "curl -s -X POST $MOON/printer/firmware_restart >/dev/null && echo '   sent'"
fi

echo "== 4. Klipper ready?"
pi "for i in \$(seq 30); do s=\$(curl -s -m 3 $MOON/printer/info | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"result\"][\"state\"])' 2>/dev/null); [ \"\$s\" = ready ] && break; sleep 2; done
echo \"   state: \${s:-no reply}\"; curl -s $MOON/printer/info | python3 -c 'import sys,json;m=json.load(sys.stdin)[\"result\"][\"state_message\"];print(\"   \"+m.splitlines()[0])' 2>/dev/null
e=\$(tac ~/printer_data/logs/klippy.log | sed '/^Start printer at/q' | tac | sed '/^===== Config file/,/^=======================$/d' | grep -iE 'error|!!|warning' | tail -10)
echo '   klippy.log errors since the restart:'; echo \"\${e:-none}\" | sed 's/^/   /'"

[ $DRY = 1 ] && exit 0
SHA=$(git -C "$ROOT" rev-parse --short HEAD)
WHAT=""; [ -n "$CFG" ] && WHAT="printer.cfg"; [ $INSTALL = 1 ] && WHAT="${WHAT:+$WHAT + }install.sh ($BRANCH)"
UNDO=""; [ -n "$CFG" ] && UNDO=" (undo: copy back \`$BAK\`)"
echo
echo "== Deploy log row (fill in the regression result, add at the top of the build/deploy log):"
echo "| $(date +%F) | **$ID**: $WHAT | klipper-ui $(git -C "$ROOT" rev-parse --abbrev-ref HEAD) $SHA | ✅ S1$UNDO | TODO | |"
