#!/usr/bin/env bash
# BENCH-ONLY deploy of the StarStack KlipperScreen fork onto the Pi's ~/KlipperScreen.
# Copies every file that differs from the fork's upstream base (added or changed),
# installs the Public Sans fonts for the Pi user, selects the theme, restarts
# KlipperScreen through Moonraker and takes a screenshot.
#
#   scripts/deploy-ks-bench.sh [screenshot.png]   deploy
#   scripts/deploy-ks-bench.sh --rollback         back to stock KlipperScreen + original KlipperScreen.conf
#
# Proper install (Pi tracks the private fork + update_manager) is a separate, later step.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FORK="${KS_FORK:-$ROOT/../KlipperScreen-starstack}"
BASE="${KS_BASE:-f580242e311005e7abfc92c3ebacf7c4b575a51d}"   # upstream commit the Pi runs
PI="$ROOT/scripts/pi.sh"
MANIFEST='~/.starstack-ks-deployed.txt'

restart_ks() {
  "$PI" 'curl -s -X POST "http://localhost:7125/machine/services/restart?service=KlipperScreen"; echo; sleep 8; systemctl is-active KlipperScreen'
}

if [ "$1" = "--rollback" ]; then
  "$PI" "cd ~/KlipperScreen && if [ -f $MANIFEST ]; then while read -r f; do git ls-files --error-unmatch \"\$f\" >/dev/null 2>&1 && git checkout -- \"\$f\" || rm -f \"\$f\"; done < $MANIFEST; rm -f $MANIFEST; fi; \
    find styles/starstack -type d -empty -delete 2>/dev/null; rm -rf styles/starstack; \
    [ -f ~/printer_data/config/KlipperScreen.conf.pre-starstack ] && cp ~/printer_data/config/KlipperScreen.conf.pre-starstack ~/printer_data/config/KlipperScreen.conf; \
    git status --short | head -20; echo 'rolled back to stock'"
  restart_ks
  exit 0
fi

SHOT="$(cd "$(dirname "${1:-.}")" 2>/dev/null && pwd)/$(basename "${1:-x}")"
cd "$FORK"
# Files added or changed vs the upstream base (committed or not), excluding deletions
FILES=$( { git diff --name-only --diff-filter=ACMR "$BASE"; git ls-files --others --exclude-standard; } | sort -u | grep -v '^FORK_CHANGES.md$' || true)
[ -n "$FILES" ] || { echo "nothing to deploy"; exit 1; }
echo "Deploying $(echo "$FILES" | wc -l) files from $(git rev-parse --short HEAD) ($(git status --porcelain | wc -l) uncommitted):"
echo "$FILES" | sed 's/^/   /'

# Pi: keep a one-time copy of the original KlipperScreen.conf
"$PI" "[ -f ~/printer_data/config/KlipperScreen.conf.pre-starstack ] || cp ~/printer_data/config/KlipperScreen.conf ~/printer_data/config/KlipperScreen.conf.pre-starstack; echo conf backup ok"
# Ship files (tar keeps paths) and record them for rollback
echo "$FILES" | tar cf - -T - | "$PI" "tar xf - -C ~/KlipperScreen && echo extracted"
echo "$FILES" | "$PI" "cat >> $MANIFEST && sort -u -o $MANIFEST $MANIFEST && echo manifest: \$(wc -l < $MANIFEST) files"
# Fonts for the Pi user (no sudo)
"$PI" 'mkdir -p ~/.local/share/fonts && cp ~/KlipperScreen/styles/starstack/fonts/*.ttf ~/.local/share/fonts/ && fc-cache -f ~/.local/share/fonts && fc-list | grep -c "Public Sans" | sed "s/^/Public Sans faces installed: /"'
# Select the theme (user section above KlipperScreen's auto-generated block)
"$PI" 'C=~/printer_data/config/KlipperScreen.conf; grep -q "^theme: starstack" $C || { printf "# STARSTACK-ADDED: StarStack theme (klipper-ui repo)\n[main]\ntheme: starstack\n\n" | cat - $C > $C.tmp && mv $C.tmp $C; }; head -4 $C'
restart_ks
[ -n "$1" ] && "$ROOT/scripts/ks-screenshot.sh" "$SHOT"
