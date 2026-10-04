#!/usr/bin/env bash
# Run a command on the BTT Pi over SSH and append the command + reply to a local log.
# Usage: scripts/pi.sh '<command>'
# Log: logs/ssh-YYYY-MM-DD.log (git-ignored: contains network details)
set -o pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${PI_HOST:-biqu@192.168.0.102}"
KEY="${PI_KEY:-$HOME/.ssh/klipper_ui_ed25519}"
LOG="$ROOT/logs/ssh-$(date +%F).log"
mkdir -p "$ROOT/logs"
{
  echo "===== $(date '+%F %T')  >>> SENT to $HOST"
  echo "$1"
  echo "----- <<< REPLY"
} >> "$LOG"
ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=10 "$HOST" "$1" 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
echo "----- exit code: $rc" >> "$LOG"
exit $rc
