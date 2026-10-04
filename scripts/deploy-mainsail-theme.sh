#!/usr/bin/env bash
# Install the StarStack Mainsail theme on the Pi.
#   scripts/deploy-mainsail-theme.sh            install / update
#   scripts/deploy-mainsail-theme.sh --rollback restore what was there before the first install
# Only touches ~/printer_data/config/.theme (Mainsail reads it, Klipper ignores it).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PI="$ROOT/scripts/pi.sh"
DEST='~/printer_data/config/.theme'
BACKUP='~/printer_data/config/.theme.pre-klipper-ui'

if [ "$1" = "--rollback" ]; then
  "$PI" "rm -rf $DEST && if [ -d $BACKUP ]; then cp -a $BACKUP $DEST && echo 'restored previous .theme'; else echo 'no previous .theme: theme removed'; fi"
  exit 0
fi

# Keep a copy of whatever existed before our first install (never overwritten)
"$PI" "if [ -d $DEST ] && [ ! -d $BACKUP ]; then cp -a $DEST $BACKUP && echo 'backed up existing .theme'; fi; mkdir -p $DEST"
for f in "$ROOT"/mainsail-theme/.theme/*; do
  name="$(basename "$f")"
  "$PI" "cat > $DEST/$name && echo \"  wrote $name (\$(wc -c < $DEST/$name) bytes)\"" < "$f"
done
"$PI" "ls -la $DEST"
echo "Done. Reload Mainsail with Ctrl+Shift+R (clears the cached theme)."
