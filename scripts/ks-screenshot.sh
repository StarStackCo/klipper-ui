#!/usr/bin/env bash
# Capture what the TFT35 (KlipperScreen) is currently showing.
# Usage: scripts/ks-screenshot.sh <output.png>
# Read-only on the Pi apart from a temp file in /tmp that is deleted afterwards.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?usage: ks-screenshot.sh <output.png>}"
"$ROOT/scripts/pi.sh" 'DISPLAY=:0 ~/.KlipperScreen-env/bin/python -c "
import gi; gi.require_version(\"Gdk\",\"3.0\"); from gi.repository import Gdk
w=Gdk.get_default_root_window(); g=w.get_geometry()
Gdk.pixbuf_get_from_window(w,0,0,g.width,g.height).savev(\"/tmp/ks.png\",\"png\",[],[]); print(\"captured\",g.width,\"x\",g.height)
"'
ssh -i "${PI_KEY:-$HOME/.ssh/klipper_ui_ed25519}" -o BatchMode=yes "${PI_HOST:-biqu@192.168.0.102}" 'cat /tmp/ks.png && rm /tmp/ks.png' > "$OUT"
echo "saved $OUT"
