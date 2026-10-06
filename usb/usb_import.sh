#!/bin/bash
# STARSTACK: mount a USB stick READ-ONLY, copy new G-code files as the printer user, unmount (D-065).
# Run as root by starstack-usb-import@<dev>.service:  usb_import.sh <dev name, e.g. sda1> <printer user>
# install.sh copies this file to /usr/local/lib/starstack/ (root-owned: a root script must not be
# editable by the printer user) and fills in @REPO@. The copier itself runs as the printer user.
# The stick is never written to, and it's unmounted again before the touchscreen asks to print,
# so it can simply be pulled out.
set -u
DEV="$1"; USER_NAME="$2"
REPO="@REPO@"
HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"
MNT="/run/starstack-usb/$DEV"
mkdir -p "$MNT"
if ! mount -o ro,nosuid,nodev,noexec "/dev/$DEV" "$MNT"; then
  echo "could not mount /dev/$DEV (unsupported filesystem?)"
  rmdir "$MNT"
  exit 0
fi
runuser -u "$USER_NAME" -- python3 "$REPO/tools/usb_import.py" "$MNT" --gcodes "$HOME_DIR/printer_data/gcodes"
umount "$MNT" || umount -l "$MNT"
rmdir "$MNT"
