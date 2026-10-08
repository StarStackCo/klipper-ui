#!/usr/bin/env bash
# StarStack printer UI installer. Run ON THE PRINTER'S PI (as the normal user, not root):
#
#   git clone https://github.com/StarStackCo/klipper-ui.git ~/klipper-ui
#   bash ~/klipper-ui/install.sh                 install / update everything (safe to re-run)
#   bash ~/klipper-ui/install.sh --dry-run       show what would change, change nothing
#   bash ~/klipper-ui/install.sh --uninstall     back to stock Mainsail + KlipperScreen
#   bash ~/klipper-ui/install.sh --fix-printer-cfg   also add the required lines to printer.cfg
#   bash ~/klipper-ui/install.sh --no-usb        skip the USB stick import (step 6, needs sudo)
#   bash ~/klipper-ui/install.sh --no-splash     skip the StarStack boot screen (step 7, needs sudo)
#   bash ~/klipper-ui/install.sh --no-fastboot   skip the faster-boot changes (step 8, needs sudo)
#   bash ~/klipper-ui/install.sh --no-update-helper   skip the update helper (step 9, needs sudo)
#   bash ~/klipper-ui/install.sh --printer=s1    this is a StarStack S1: the update helper also keeps
#                                                its board firmware current (remembered on re-runs)
#
# What it does (each step prints what it changed; backups are made once, never overwritten):
#   1. Links the StarStack macros and Mainsail theme from this repo into ~/printer_data/config
#      (so Mainsail's update manager updates them with one click)
#   2. Checks printer.cfg has what the UI needs (and adds it with --fix-printer-cfg)
#   3. Adds [update_manager klipper-ui] and points [update_manager KlipperScreen] at the StarStack fork,
#      includes the tested Klipper/Moonraker versions (update/versions.conf, D-087) and removes the
#      update entries of add-ons the printer doesn't use (timelapse, print_area_bed_mesh, and the
#      webcam streamer and Wi-Fi keepalive when they're switched off)
#   4. Switches ~/KlipperScreen to the StarStack fork (re-clones if the git folder is damaged),
#      installs the Public Sans font and selects the starstack theme
#   5. Applies Mainsail UI settings + macro groups + dashboard panel order (Moonraker database)
#   6. USB stick import: plugging in a stick copies new G-code files into the print jobs folder
#      (udev rule + service, asks for your password once via sudo; skip with --no-usb)
#   7. Boot screen: StarStack logo on the touchscreen from power-up until the UI starts, at
#      shutdown and while the UI restarts; kernel text goes to the serial port only, Plymouth off
#      (/boot/armbianEnv.txt, backed up), and the touchscreen app starts without waiting for the
#      network (KlipperScreen.service, backed up). sudo; skip with --no-splash. Needs a reboot
#   8. Faster boot: Klipper and Moonraker start without waiting for the network
#      (klipper/moonraker.service, backed up); turns off unused services (webcam streamer
#      crowsnest, OpenVPN, NFS, keyboard/console setup) and automatic OS updates; the
#      touchscreen's X server no longer loads OpenGL (/etc/X11/xorg.conf.d). sudo; skip with
#      --no-fastboot; --uninstall turns them back on. Needs a reboot
#   9. Update helper (starstack-update.service, sudo; skip with --no-update-helper): one "Update
#      everything" tap also installs newly tested Klipper/Moonraker versions and, with --printer,
#      brings the board firmware to the same Klipper version (Katapult). Also holds the kernel,
#      bootloader and board packages (update/held-packages.txt), so "Update everything" can't
#      install an untested one that stops the Pi booting (D-092)
#  10. Restarts Moonraker, Klipper and KlipperScreen
# It refuses to run while a print is in progress.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="${PRINTER_CONFIG:-$HOME/printer_data/config}"
MOON="http://localhost:7125"
KS_DIR="$HOME/KlipperScreen"
KS_FORK="https://github.com/StarStackCo/KlipperScreen-starstack.git"
KS_UP="https://github.com/KlipperScreen/KlipperScreen.git"
UI_ORIGIN="https://github.com/StarStackCo/klipper-ui.git"
DRY=0; MODE=install; FIX_CFG=0; USB=1; SPLASH=1; FASTBOOT=1; HELPER=1; PRINTER=""
for a in "$@"; do
  case "$a" in
    --no-update-helper) HELPER=0 ;;
    --printer=*) PRINTER="${a#--printer=}" ;;
    --dry-run) DRY=1 ;;
    --uninstall) MODE=uninstall ;;
    --fix-printer-cfg) FIX_CFG=1 ;;
    --no-usb) USB=0 ;;
    --no-splash) SPLASH=0 ;;
    --no-fastboot) FASTBOOT=0 ;;
    -h|--help) sed -n '2,41p' "$0"; exit 0 ;;
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
  [ "$DRY" = 1 ] && { echo "   (dry-run) update [update_manager klipper-ui] and [update_manager KlipperScreen], include the tested versions, drop unused add-on entries"; return; }
  # webcam streamer off: step 8 turns it off (no camera), or it already is
  local cam_off=0
  { [ "$FASTBOOT" = 1 ] || [ "$(systemctl is-enabled crowsnest 2>/dev/null)" != enabled ]; } && cam_off=1
  python3 - "$CFG/moonraker.conf" "$REPO" "$UI_ORIGIN" "$KS_FORK" "$CFG/printer.cfg" "$cam_off" "$CFG/sonar.conf" <<'PY'
import re, sys
p, repo, ui_origin, ks_fork, printer_cfg, cam_off, sonar_conf = sys.argv[1:]
s = open(p).read()
try:
    pcfg = open(printer_cfg).read()
except OSError:
    pcfg = ''
def section(name):
    return re.search(r'^\[%s\]\n(.*?)(?=^\[|\Z)' % re.escape(name), s, re.S | re.M)
ui = ('[update_manager klipper-ui]\n'
      '# STARSTACK-ADDED: StarStack macros + Mainsail theme (klipper-ui install.sh)\n'
      'type: git_repo\npath: %s\norigin: %s\nprimary_branch: main\nmanaged_services: klipper moonraker\n\n' % (repo, ui_origin))
m = section('update_manager klipper-ui')
s = s[:m.start()] + ui + s[m.end():] if m else s.rstrip('\n') + '\n\n' + ui
m = section('update_manager KlipperScreen')
if m:
    body = re.sub(r'^(origin|primary_branch):.*\n|^# STARSTACK.*\n', '', m.group(1), flags=re.M)
    body = ('# STARSTACK-ADDED: track the public StarStack fork (klipper-ui install.sh)\n'
            'origin: %s\nprimary_branch: starstack\n' % ks_fork) + body
    s = s[:m.start(1)] + body + s[m.end(1):]
# Update entries of add-ons this printer doesn't load only offer untested updates (D-087)
try:
    sonar_off = re.search(r'^\s*enable:\s*false', open(sonar_conf).read(), re.M | re.I) is not None
except OSError:
    sonar_off = True
unused = {'timelapse': 'timelapse.cfg' not in pcfg and not section('timelapse'),
          'print_area_bed_mesh': 'print_area_bed_mesh' not in pcfg,
          'crowsnest': cam_off == '1',  # the Camera switch (B-9) adds it back when a camera is fitted
          'sonar': sonar_off}
for name, drop in unused.items():
    m = section('update_manager ' + name)
    if m and drop:
        s = s[:m.start()] + s[m.end():]
        print('   moonraker.conf: removed [update_manager %s] (not used by this printer)' % name)
# their installers' label comments ("# Crowsnest update_manager entry"), now above another section
s = re.sub(r'^# (\w+) update_manager entry\n(?!\[update_manager \1\])', '', s, flags=re.M | re.I)
# Tested Klipper/Moonraker versions (update/versions.conf): last, so its values win
inc = '[include starstack-updates.conf]'
if inc not in s:
    s = s.rstrip('\n') + '\n\n' + inc + '\n'
s = re.sub(r'\n{3,}', '\n\n', s)
open(p, 'w').write(s)
print('   moonraker.conf: [update_manager klipper-ui] + KlipperScreen -> StarStack fork, tested versions')
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
  # Same channel as this repo: klipper-ui dev (bench testing) pairs with the fork's dev branch,
  # otherwise the stable starstack branch (D-072: a dev klipper-ui with the stable app broke the
  # boot bar)
  local KS_BRANCH=starstack
  [ "$(git -C "$REPO" branch --show-current 2>/dev/null)" = dev ] && KS_BRANCH=dev
  if [ ! -d "$KS_DIR" ]; then echo "   KlipperScreen not installed: install it with KIAUH first, then re-run"; return; fi
  if ! git -C "$KS_DIR" fsck --no-dangling >/dev/null 2>&1; then
    local b="$KS_DIR.corrupt-$(date +%Y%m%d-%H%M)"
    echo "   KlipperScreen git folder is damaged: keeping it as $b and re-cloning"
    do_ "mv '$KS_DIR' '$b' && git clone -q -b starstack '$KS_FORK' '$KS_DIR'"
  fi
  do_ "git -C '$KS_DIR' remote set-url origin '$KS_FORK'"
  git -C "$KS_DIR" remote get-url upstream >/dev/null 2>&1 || do_ "git -C '$KS_DIR' remote add upstream '$KS_UP'"
  do_ "git -C '$KS_DIR' remote set-url --push upstream DISABLED"
  do_ "git -C '$KS_DIR' fetch -q --tags origin && git -C '$KS_DIR' checkout -q -f -B $KS_BRANCH origin/$KS_BRANCH && git -C '$KS_DIR' branch -q -u origin/$KS_BRANCH"
  [ "$DRY" = 1 ] || echo "   KlipperScreen: $(git -C "$KS_DIR" describe --tags --always) on $KS_BRANCH"
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

USB_LIB=/usr/local/lib/starstack/usb_import.sh
USB_UNIT=/etc/systemd/system/starstack-usb-import@.service
USB_RULE=/etc/udev/rules.d/99-starstack-usb.rules

usb_install() {  # root-owned copies: the wrapper runs as root, so the printer user must not be able to edit it
  local tmp; tmp=$(mktemp -d)
  sed "s|@REPO@|$REPO|g" "$REPO/usb/usb_import.sh" > "$tmp/usb_import.sh"
  sed "s|@USER@|$(id -un)|g" "$REPO/usb/starstack-usb-import@.service" > "$tmp/unit"
  if cmp -s "$tmp/usb_import.sh" "$USB_LIB" && cmp -s "$tmp/unit" "$USB_UNIT" && cmp -s "$REPO/usb/99-starstack-usb.rules" "$USB_RULE"; then
    echo "   ok: USB stick import already installed"; rm -rf "$tmp"; return
  fi
  echo "   installing USB stick import (sudo may ask for your password)"
  do_ "sudo install -D -o root -g root -m 755 '$tmp/usb_import.sh' '$USB_LIB'"
  do_ "sudo install -o root -g root -m 644 '$tmp/unit' '$USB_UNIT'"
  do_ "sudo install -o root -g root -m 644 '$REPO/usb/99-starstack-usb.rules' '$USB_RULE'"
  do_ "sudo systemctl daemon-reload && sudo udevadm control --reload-rules"
  rm -rf "$tmp"
  echo "   USB stick import installed: new G-code files are copied to ~/printer_data/gcodes"
}

usb_remove() {
  if [ -e "$USB_RULE" ] || [ -e "$USB_UNIT" ] || [ -e "$USB_LIB" ]; then
    do_ "sudo rm -f '$USB_RULE' '$USB_UNIT' '$USB_LIB' && sudo systemctl daemon-reload && sudo udevadm control --reload-rules"
    echo "   USB stick import removed"
  fi
}

SPL_LIB=/usr/local/lib/starstack/starstack-splash.sh
SPL_BAR=/usr/local/lib/starstack/starstack-bootbar.py
SPL_STATE=/var/lib/starstack
SPL_IMG=/usr/local/share/starstack/starstack-splash.rgb565
SPL_SHARE=/usr/local/share/starstack
SPL_BOOT="starstack-splash-boot.rgb565 starstack-splash-boot.png starstack-splash-fail.rgb565
  starstack-glyphs.rgb565 starstack-glyphs.json"  # boot/restart images (D-073), app-failed screen (D-079)
SPL_UNIT=/etc/systemd/system/starstack-splash.service
SPL_DROP=/etc/systemd/system/KlipperScreen.service.d/starstack-splash.conf
ARMENV=/boot/armbianEnv.txt
KS_UNIT=/etc/systemd/system/KlipperScreen.service

splash_install() {
  if [ "$(cat /sys/class/graphics/fb0/virtual_size 2>/dev/null)" != "480,320" ]; then
    echo "   skipped: the touchscreen isn't a 480x320 TFT35 (the splash is made for that size)"; return
  fi
  local changed=0
  cmp -s "$REPO/splash/starstack-splash.sh" "$SPL_LIB" || changed=1
  cmp -s "$REPO/splash/starstack-bootbar.py" "$SPL_BAR" || changed=1
  [ -d "$SPL_STATE" ] || changed=1
  cmp -s "$REPO/splash/starstack-splash.rgb565" "$SPL_IMG" || changed=1
  for f in $SPL_BOOT; do cmp -s "$REPO/splash/$f" "$SPL_SHARE/$f" || changed=1; done
  cmp -s "$REPO/splash/starstack-splash.service" "$SPL_UNIT" || changed=1
  cmp -s "$REPO/splash/klipperscreen-splash.conf" "$SPL_DROP" || changed=1
  if [ $changed = 1 ]; then
    echo "   installing the boot screen (sudo may ask for your password)"
    do_ "sudo install -D -o root -g root -m 755 '$REPO/splash/starstack-splash.sh' '$SPL_LIB'"
    do_ "sudo install -D -o root -g root -m 755 '$REPO/splash/starstack-bootbar.py' '$SPL_BAR'"
    do_ "sudo install -d -o $(id -un) -g $(id -gn) -m 755 '$SPL_STATE'"  # boot time, written by the touchscreen app
    do_ "sudo install -D -o root -g root -m 644 '$REPO/splash/starstack-splash.rgb565' '$SPL_IMG'"
    for f in $SPL_BOOT; do do_ "sudo install -o root -g root -m 644 '$REPO/splash/$f' '$SPL_SHARE/$f'"; done
    do_ "sudo install -o root -g root -m 644 '$REPO/splash/starstack-splash.service' '$SPL_UNIT'"
    do_ "sudo install -D -o root -g root -m 644 '$REPO/splash/klipperscreen-splash.conf' '$SPL_DROP'"
    do_ "sudo systemctl daemon-reload && sudo systemctl enable starstack-splash.service"
  else
    echo "   ok: boot screen files installed"
  fi
  # No login prompt drawn over the logo on the touchscreen's console (SSH and serial still work)
  if [ "$(systemctl is-enabled getty@tty1 2>/dev/null)" != masked ]; then
    do_ "sudo systemctl mask getty@tty1.service autovt@tty1.service"
    echo "   touchscreen login prompt turned off (getty@tty1 masked)"
  fi
  # Kernel/boot text to the serial port only, no blinking cursor, no Plymouth (it blanked the
  # logo until the UI started, D-069) (Armbian boot options)
  if [ -f "$ARMENV" ]; then
    if grep -q '^console=cancel_lcd' "$ARMENV" && grep -q 'vt.global_cursor_default=0' "$ARMENV" \
      && grep -q 'plymouth.enable=0' "$ARMENV"; then
      echo "   ok: boot text already off the touchscreen"
    else
      [ -e "$ARMENV.pre-starstack" ] || do_ "sudo cp -a '$ARMENV' '$ARMENV.pre-starstack'"
      do_ "sudo sed -i 's/^console=.*/console=cancel_lcd/' '$ARMENV'"
      grep -q '^console=' "$ARMENV" || do_ "echo 'console=cancel_lcd' | sudo tee -a '$ARMENV' >/dev/null"
      grep -q '^extraargs=' "$ARMENV" || do_ "echo 'extraargs=' | sudo tee -a '$ARMENV' >/dev/null"
      for arg in vt.global_cursor_default=0 plymouth.enable=0; do
        grep -q "$arg" "$ARMENV" || do_ "sudo sed -i 's/^extraargs=\(.*\)/extraargs=\1 $arg/' '$ARMENV'"
      done
      echo "   boot text moved off the touchscreen ($ARMENV, backup: $ARMENV.pre-starstack). Reboot to see it"
    fi
  fi
  # Start the touchscreen app without waiting for the network and Moonraker (D-069)
  if [ -f "$KS_UNIT" ] && ! grep -q 'StarStack (D-069)' "$KS_UNIT"; then
    [ -e "$KS_UNIT.pre-starstack" ] || do_ "sudo cp -a '$KS_UNIT' '$KS_UNIT.pre-starstack'"
    do_ "sudo sed -i -f '$REPO/splash/klipperscreen-unit.sed' '$KS_UNIT' && sudo systemctl daemon-reload"
    echo "   touchscreen app now starts early in the boot ($KS_UNIT, backup: $KS_UNIT.pre-starstack)"
  fi
}

splash_remove() {
  if [ -e "$SPL_UNIT" ] || [ -e "$SPL_DROP" ]; then
    do_ "sudo systemctl disable starstack-splash.service 2>/dev/null; sudo rm -rf '$SPL_UNIT' '$SPL_DROP' '$SPL_LIB' '$SPL_BAR' '$SPL_SHARE' '$SPL_STATE' && sudo systemctl daemon-reload"
    echo "   boot screen removed"
  fi
  if [ "$(systemctl is-enabled getty@tty1 2>/dev/null)" = masked ]; then
    do_ "sudo systemctl unmask getty@tty1.service autovt@tty1.service"
  fi
  if [ -e "$ARMENV.pre-starstack" ]; then
    do_ "sudo mv '$ARMENV.pre-starstack' '$ARMENV'"; echo "   restored $ARMENV (reboot to apply)"
  fi
  if [ -e "$KS_UNIT.pre-starstack" ]; then
    do_ "sudo mv '$KS_UNIT.pre-starstack' '$KS_UNIT' && sudo systemctl daemon-reload"
    echo "   restored $KS_UNIT"
  fi
}

# ---- 8. Faster boot (D-075)
FB_UNITS="/etc/systemd/system/klipper.service /etc/systemd/system/moonraker.service"
FB_XCONF=/etc/X11/xorg.conf.d/10-starstack-noglx.conf  # X without OpenGL (D-076)
FB_LIST=/var/lib/starstack/disabled-services  # what this step turned off, so --uninstall can undo it
# Unused on a StarStack printer: webcam streamer (no camera: it fails after ~5 s of CPU every boot),
# OpenVPN (not configured), NFS client, keyboard/console setup (no keyboard or text console), and
# automatic OS updates (updates are done on purpose, not in the background on a printer)
FB_OFF="crowsnest.service openvpn.service rpcbind.service rpcbind.socket nfs-client.target
  keyboard-setup.service console-setup.service
  unattended-upgrades.service apt-daily.timer apt-daily-upgrade.timer"

fastboot_install() {
  local u reload=0
  for u in $FB_UNITS; do
    [ -f "$u" ] || continue
    if grep -q 'StarStack (D-075)' "$u"; then
      echo "   ok: $(basename "$u") starts without waiting for the network"
    else
      [ -e "$u.pre-starstack" ] || do_ "sudo cp -a '$u' '$u.pre-starstack'"
      do_ "sudo sed -i -f '$REPO/boot/no-network-wait.sed' '$u'"
      reload=1
      echo "   $(basename "$u") no longer waits for the network (backup: $u.pre-starstack)"
    fi
  done
  if cmp -s "$REPO/boot/10-starstack-noglx.conf" "$FB_XCONF"; then
    echo "   ok: touchscreen display server starts without OpenGL"
  else
    do_ "sudo install -D -o root -g root -m 644 '$REPO/boot/10-starstack-noglx.conf' '$FB_XCONF'"
    echo "   touchscreen display server no longer loads OpenGL (~5 s faster)"
  fi
  [ -d /var/lib/starstack ] || do_ "sudo install -d -o $(id -un) -g $(id -gn) -m 755 /var/lib/starstack"
  for u in $FB_OFF; do
    if [ "$(systemctl is-enabled "$u" 2>/dev/null)" = enabled ]; then
      do_ "sudo systemctl disable --now '$u' 2>/dev/null; echo '$u' >> '$FB_LIST'"
      echo "   turned off $u"
      reload=1
    fi
  done
  [ $reload = 0 ] || do_ "sudo systemctl daemon-reload"  # nothing to do = no password prompt
  # crowsnest: if a camera is added later, re-enable with: sudo systemctl enable --now crowsnest
}

fastboot_remove() {
  local u
  [ -e "$FB_XCONF" ] && do_ "sudo rm -f '$FB_XCONF'" && echo "   removed $FB_XCONF"
  for u in $FB_UNITS; do
    if [ -e "$u.pre-starstack" ]; then
      do_ "sudo mv '$u.pre-starstack' '$u'"; echo "   restored $u"
    fi
  done
  if [ -f "$FB_LIST" ]; then
    for u in $(sort -u "$FB_LIST"); do do_ "sudo systemctl enable '$u' 2>/dev/null || true"; done
    do_ "rm -f '$FB_LIST'"; echo "   turned the services back on (reboot to start them)"
  fi
  do_ "sudo systemctl daemon-reload"
}

# ---- 9. Update helper (D-087)
UPD_LIB=/usr/local/lib/starstack/starstack-update.py
UPD_UNIT=/etc/systemd/system/starstack-update.service
UPD_PRINTER=/var/lib/starstack/printer  # which config/<printer>/firmware.conf the helper uses

helper_install() {
  local tmp changed=0
  tmp=$(mktemp -d)
  sed -e "s|@USER@|$(id -un)|g" -e "s|@REPO@|$REPO|g" "$REPO/update/starstack-update.service" > "$tmp/unit"
  cmp -s "$REPO/update/starstack-update.py" "$UPD_LIB" || changed=1
  cmp -s "$tmp/unit" "$UPD_UNIT" || changed=1
  [ -d /var/lib/starstack ] || changed=1
  if [ $changed = 1 ]; then
    echo "   installing the update helper (sudo may ask for your password)"
    do_ "sudo install -D -o root -g root -m 755 '$REPO/update/starstack-update.py' '$UPD_LIB'"
    do_ "sudo install -o root -g root -m 644 '$tmp/unit' '$UPD_UNIT'"
    [ -d /var/lib/starstack ] || do_ "sudo install -d -o $(id -un) -g $(id -gn) -m 755 /var/lib/starstack"
    do_ "sudo systemctl daemon-reload && sudo systemctl enable starstack-update.service"
  else
    echo "   ok: update helper installed"
  fi
  rm -rf "$tmp"
  # --printer=<name> is remembered; the helper only flashes boards with a config/<name>/firmware.conf
  if [ -n "$PRINTER" ]; then
    if [ -f "$REPO/config/$PRINTER/firmware.conf" ]; then
      [ "$(cat "$UPD_PRINTER" 2>/dev/null)" = "$PRINTER" ] || do_ "echo '$PRINTER' > '$UPD_PRINTER'"
    else
      echo "   no config/$PRINTER/firmware.conf in klipper-ui: board firmware updates stay off"
    fi
  fi
  if [ -s "$UPD_PRINTER" ]; then
    echo "   board firmware: kept at the host's Klipper version ($(cat "$UPD_PRINTER"))"
  else
    echo "   board firmware: not managed (add --printer=s1 on a StarStack S1)"
  fi
  [ $changed = 1 ] && do_ "sudo systemctl restart starstack-update.service" || true
  held_install
}

HELD_LIST=/var/lib/starstack/held-packages  # packages this installer put on hold (for --uninstall)

held_install() {
  local pat p want=() missing=() held
  while read -r pat; do
    case "$pat" in ''|'#'*) continue ;; esac
    while read -r p; do want+=("$p"); done < <(dpkg-query -W -f='${db:Status-Abbrev} ${Package}\n' "$pat" 2>/dev/null | awk '$1 == "ii" {print $2}')
  done < "$REPO/update/held-packages.txt"
  held=$(apt-mark showhold)
  for p in "${want[@]}"; do grep -qx "$p" <<< "$held" || missing+=("$p"); done
  if [ ${#missing[@]} -gt 0 ]; then
    echo "   holding kernel/boot packages so updates skip them: ${missing[*]}"
    do_ "sudo apt-mark hold ${missing[*]} >/dev/null && printf '%s\n' ${missing[*]} >> '$HELD_LIST'"
  else
    echo "   ok: kernel/boot packages held (${#want[@]})"
  fi
}

held_remove() {
  if [ -s "$HELD_LIST" ]; then
    do_ "sudo apt-mark unhold $(sort -u "$HELD_LIST" | tr '\n' ' ') >/dev/null && rm -f '$HELD_LIST'"
    echo "   kernel/boot packages no longer held"
  fi
}

helper_remove() {
  if [ -e "$UPD_UNIT" ] || [ -e "$UPD_LIB" ]; then
    do_ "sudo systemctl disable --now starstack-update.service 2>/dev/null; sudo rm -f '$UPD_UNIT' '$UPD_LIB' && sudo systemctl daemon-reload"
    echo "   update helper removed"
  fi
}

if [ "$MODE" = uninstall ]; then
  say "Uninstall StarStack UI"
  unlink_restore starstack_macros.cfg
  unlink_restore .theme
  for f in moonraker.conf KlipperScreen.conf; do
    [ -e "$CFG/$f.pre-starstack" ] && do_ "cp '$CFG/$f.pre-starstack' '$CFG/$f'" && echo "   restored $f"
  done
  # after moonraker.conf is restored: it no longer includes this file
  [ -L "$CFG/starstack-updates.conf" ] && do_ "rm '$CFG/starstack-updates.conf'"
  held_remove
  helper_remove
  if [ -d "$KS_DIR" ]; then
    do_ "git -C '$KS_DIR' remote set-url origin '$KS_UP' && git -C '$KS_DIR' fetch -q origin && git -C '$KS_DIR' checkout -q -f -B master origin/master"
  fi
  [ "$DRY" = 1 ] || python3 "$REPO/tools/apply_mainsail.py" --rollback
  echo "   printer.cfg was not changed: remove the StarStack lines by hand if you added them"
  usb_remove
  fastboot_remove  # before splash_remove: its list lives in /var/lib/starstack
  splash_remove
  restart_all
  exit 0
fi

say "1/10 Link StarStack macros + Mainsail theme"
link macros/starstack_macros.cfg starstack_macros.cfg
link mainsail-theme/.theme .theme
link update/versions.conf starstack-updates.conf  # before step 3 includes it in moonraker.conf
say "2/10 Check printer.cfg"
printer_cfg_check
say "3/10 Moonraker update manager"
moonraker_sections
say "4/10 KlipperScreen -> StarStack fork"
klipperscreen_fork
say "5/10 Mainsail settings + macro groups + panel order"
if [ "$DRY" = 1 ]; then echo "   (dry-run) apply mainsail-theme/settings.json + macrogroups.json + dashboard.json"; else python3 "$REPO/tools/apply_mainsail.py" | sed 's/^/   /'; fi
say "6/10 USB stick import"
if [ "$USB" = 1 ]; then usb_install; else echo "   skipped (--no-usb)"; fi
say "7/10 Boot screen"
if [ "$SPLASH" = 1 ]; then splash_install; else echo "   skipped (--no-splash)"; fi
say "8/10 Faster boot"
if [ "$FASTBOOT" = 1 ]; then fastboot_install; else echo "   skipped (--no-fastboot)"; fi
say "9/10 Update helper"
if [ "$HELPER" = 1 ]; then helper_install; else echo "   skipped (--no-update-helper)"; fi
say "10/10 Restart services"
restart_all
say "Done. Update from the touchscreen (Settings > Updates > Update everything) or Mainsail (Machine > Update Manager)."
