#!/bin/sh
# STARSTACK: draw the StarStack logo on the touchscreen framebuffer (D-068, D-073).
# Installed to /usr/local/lib/starstack/ by install.sh.
#   starstack-splash.sh boot      at boot: logo + bar, then starstack-bootbar.py fills the bar
#   starstack-splash.sh restart   the touchscreen app stopped (KlipperScreen drop-in): logo + empty
#                                 bar, the app's "Starting printer" cover continues from there;
#                                 the bar program's watchdog notices if the app doesn't come back
#   starstack-splash.sh           shutdown / power-off: logo only
# Only draws on the TFT35 (480x320, 16 bit) the images were made for; otherwise does nothing.
SHARE=/usr/local/share/starstack
FB=/sys/class/graphics/fb0
IMG=$SHARE/starstack-splash.rgb565
[ "$1" = boot ] || [ "$1" = restart ] && IMG=$SHARE/starstack-splash-boot.rgb565
# The app stopped: tell the boot bar program's watchdog it's no longer up (D-080)
[ "$1" = restart ] && rm -f /run/starstack/ui-up
i=0
while [ ! -e /dev/fb0 ] && [ $i -lt 100 ]; do sleep 0.2; i=$((i + 1)); done  # driver may load late
[ "$(cat $FB/virtual_size 2>/dev/null)" = "480,320" ] || exit 0
[ "$(cat $FB/bits_per_pixel 2>/dev/null)" = "16" ] || exit 0
# Detach the Linux text console from the screen (needs root, so only at boot/shutdown; D-069).
# Otherwise it paints its empty black console over the logo whenever X starts or stops.
for v in /sys/class/vtconsole/vtcon*; do
  grep -q "frame buffer" "$v/name" 2>/dev/null && echo 0 > "$v/bind" 2>/dev/null
done
cat "$IMG" > /dev/fb0 2>/dev/null
# At boot: fill the bar until the touchscreen app is up (D-070)
BAR=/usr/local/lib/starstack/starstack-bootbar.py
[ "$1" = boot ] && [ -x /usr/bin/python3 ] && [ -f "$BAR" ] && exec /usr/bin/python3 "$BAR"
exit 0
