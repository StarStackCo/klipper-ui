#!/bin/sh
# STARSTACK: draw the StarStack logo on the touchscreen framebuffer (D-068).
# Installed to /usr/local/lib/starstack/ by install.sh. Used at boot and shutdown
# (starstack-splash.service) and whenever KlipperScreen stops/restarts (service drop-in).
# Only draws on the TFT35 (480x320, 16 bit) the image was made for; otherwise does nothing.
IMG=/usr/local/share/starstack/starstack-splash.rgb565
FB=/sys/class/graphics/fb0
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
# At boot: progress bar under the logo until the touchscreen app is up (D-070)
BAR=/usr/local/lib/starstack/starstack-bootbar.py
[ "$1" = boot ] && [ -x /usr/bin/python3 ] && [ -f "$BAR" ] && exec /usr/bin/python3 "$BAR"
exit 0
