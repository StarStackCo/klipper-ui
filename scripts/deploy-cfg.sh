#!/usr/bin/env bash
# Deploy printer.cfg and/or the installer (macros, theme) to the Pi the way
# .claude/skills/printer-config/deploy-to-pi.md says, then check Klipper and print a deploy log row.
#   scripts/deploy-cfg.sh D-NNN [--cfg [file]] [--install [--branch dev]] [--dry-run]
#   --cfg      copy config/s1/printer.cfg, the production standard (or the given file; the prototype takes
#              config/s1-proto/printer.cfg) over the Pi's printer.cfg, keeping the Pi's
#              SAVE_CONFIG block; the old file is kept as printer.cfg.pre-dnnn
#   --install  scripts/pi-install.sh --branch <branch> (macros, theme; install.sh restarts everything)
#   --dry-run  show the Pi commands without running them
# Refuses while a print is printing or paused (a restart ends the print). Every Pi command goes through pi.sh.
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PI="$ROOT/scripts/pi.sh"
MOON=http://localhost:7125
PROTO_SERIAL=E6647C7403679636   # the prototype S1's Micro4
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
BAK="printer.cfg.pre-$(echo "$ID" | tr -d '-' | tr 'A-Z' 'a-z')"

pi() { if [ $DRY = 1 ]; then echo "(dry-run) pi.sh: $1"; else "$PI" "$1"; fi; }

echo "== 1. Printer must be idle"
STATE=$("$PI" "curl -s -m 5 '$MOON/printer/objects/query?print_stats' | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"result\"][\"status\"][\"print_stats\"][\"state\"])' 2>/dev/null || echo unknown")
echo "   print_stats.state: $STATE"
if [ "$STATE" = printing ] || [ "$STATE" = paused ]; then echo "A print is $STATE. Deploy when it ends."; exit 1; fi

if [ -n "$CFG" ]; then
  echo "== 2. printer.cfg from ${CFG#"$ROOT"/} (backup ~/printer_data/config/$BAK)"
  # Printer type guard (D-NEW type guard): config/<type>/printer.cfg only goes on a Pi installed with
  # install.sh --printer=<type> (/var/lib/starstack/printer); config/bench only on a Pi with no type.
  WANT=$(basename "$(dirname "$CFG")"); [ "$WANT" = bench ] && WANT=""
  PIINFO=$("$PI" "cat /var/lib/starstack/printer 2>/dev/null; echo; [ -e ~/printer_data/config/starstack_s1_common.cfg ] && echo has-common; ls /dev/serial/by-id/ 2>/dev/null | grep -q '$PROTO_SERIAL' && echo proto-board; true")
  TYPE=$(echo "$PIINFO" | sed -n 1p | tr -d '[:space:]')
  echo "   printer type on the Pi: ${TYPE:-none}, file is for: ${WANT:-bench}"
  if [ "$TYPE" != "$WANT" ]; then
    echo "Wrong printer: this Pi is type '${TYPE:-none}', the file is for '${WANT:-bench}'."
    echo "Deploy config/${TYPE:-bench}/printer.cfg, or set the type with install.sh --printer=<type> (sudo)."; exit 1; fi
  # Second guard: the prototype's board is plugged in (USB id), in case its type is still the old 's1'.
  if ! grep -q "$PROTO_SERIAL" "$CFG" && echo "$PIINFO" | grep -q proto-board; then
    echo "This Pi runs the prototype S1's board: deploy config/s1-proto/printer.cfg to it."; exit 1; fi
  if grep -q '^\[include starstack_s1_common.cfg\]' "$CFG" && ! echo "$PIINFO" | grep -q has-common; then
    if [ $INSTALL = 0 ]; then
      echo "The Pi has no starstack_s1_common.cfg yet: add --install (klipper-ui with the shared file) first."; exit 1; fi
    git -C "$ROOT" fetch -q origin "$BRANCH" 2>/dev/null || true
    if ! git -C "$ROOT" cat-file -e "origin/$BRANCH:config/s1_common.cfg" 2>/dev/null; then
      echo "Branch '$BRANCH' on GitHub has no config/s1_common.cfg: installing it would leave Klipper without the shared file."; exit 1; fi
  fi
  if [ $DRY = 1 ]; then echo "(dry-run) upload $(sha256sum "$CFG" | cut -c1-12), keep SAVE_CONFIG block"
  else
    # Repo file with the Pi's own SAVE_CONFIG block (PID, probe, mesh); a new Pi with no block keeps the repo's
    # starting PID, without which Klipper won't start.
    # Klipper's marker is "#*# <----------------------- SAVE_CONFIG ----...>"; the old 4-dash pattern never matched.
    M='^#\*# <-* SAVE_CONFIG -*>'
    "$PI" "cat > /tmp/printer.cfg.new && cd ~/printer_data/config &&
      { [ -e $BAK ] && echo '   backup $BAK already exists, kept' || { [ ! -e printer.cfg ] || cp -p printer.cfg $BAK; }; } &&
      if grep -q '$M' printer.cfg 2>/dev/null; then
        sed -i '/$M/,\$d' /tmp/printer.cfg.new &&
        sed -n '/$M/,\$p' printer.cfg >> /tmp/printer.cfg.new
      else echo '   no SAVE_CONFIG block on the Pi: keeping the repo starting values'; fi &&
      cp /tmp/printer.cfg.new printer.cfg && rm /tmp/printer.cfg.new &&
      echo \"   installed, \$(grep -c '^#\*#' printer.cfg) SAVE_CONFIG lines in place\"" < "$CFG"
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
# the board's sensor range check fires a few seconds after ready (unplugged sensor, ADC out of range): look again
[ \"\$s\" = ready ] && sleep 6 && s=\$(curl -s -m 3 $MOON/printer/info | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"result\"][\"state\"])' 2>/dev/null)
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
