#!/usr/bin/env python3
"""Build the StarStack KlipperScreen theme into the fork.

    python scripts/build_ks_theme.py <path-to-KlipperScreen-starstack> <vendor-dir>

<vendor-dir> must contain the official release zips:
    ps.zip  = uswds/public-sans v2.001        (OFL-1.1)
    bi.zip  = twbs/icons bootstrap-icons 1.13.1 (MIT)

Output (all NEW files, no upstream file is touched):
    styles/starstack/style.css    brand colours + font (built from klipper-ui/klipperscreen/style.css)
    styles/starstack/style.conf   graph colours
    styles/starstack/images/*.svg Bootstrap icons recoloured for GdkPixbuf, plus
                                  material-dark icons for names Bootstrap has no match for
    styles/starstack/fonts/*.ttf  Public Sans (installed on the Pi by scripts/install_ks_fonts.sh)
    styles/starstack/LICENSES.md  third-party licences
"""
import os, re, shutil, sys, zipfile, json

FORK, VENDOR = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(FORK, "styles", "starstack")
IMG = os.path.join(OUT, "images")

WHITE, SKY, ACCENT, HOT, ERR, OK_ = "#FAFAFA", "#88D8F2", "#00ACC7", "#FF8904", "#FF6467", "#5CA300"

# KlipperScreen icon name -> (Bootstrap icon, colour). Names not listed keep the
# material-dark artwork (printer-specific drawings Bootstrap has no match for).
MAP = {
    "main": ("house", WHITE), "home": ("house-door", WHITE), "back": ("arrow-left", WHITE),
    "arrow-up": ("arrow-up", WHITE), "arrow-down": ("arrow-down", WHITE),
    "arrow-left": ("arrow-left", WHITE), "arrow-right": ("arrow-right", WHITE),
    "emergency": ("exclamation-octagon-fill", "#FFFFFF"), "shutdown": ("power", WHITE),
    "settings": ("gear", WHITE), "files": ("folder2-open", WHITE), "file": ("file-earmark", WHITE),
    "folder": ("folder", WHITE), "printer": ("printer", WHITE), "move": ("arrows-move", WHITE),
    "fan": ("fan", WHITE), "fan-on": ("fan", SKY), "heat-up": ("thermometer-high", HOT),
    "heater": ("thermometer-half", HOT), "cool-down": ("snow", SKY), "pause": ("pause-fill", WHITE),
    "resume": ("play-fill", WHITE), "stop": ("stop-fill", ERR), "cancel": ("x-circle", ERR),
    "refresh": ("arrow-clockwise", WHITE), "delete": ("trash", WHITE), "info": ("info-circle", WHITE),
    "console": ("terminal", WHITE), "clock": ("clock", WHITE), "hourglass": ("hourglass-split", WHITE),
    "lock": ("lock-fill", HOT), "increase": ("plus-lg", WHITE), "decrease": ("dash-lg", WHITE),
    "complete": ("check-circle-fill", OK_), "network": ("wifi", WHITE),
    "wifi_excellent": ("wifi", WHITE), "wifi_good": ("wifi-2", WHITE), "wifi_fair": ("wifi-1", WHITE),
    "wifi_weak": ("wifi-off", HOT), "light": ("lightbulb", WHITE), "camera": ("camera", WHITE),
    "sd": ("sd-card", WHITE), "warning": ("exclamation-triangle-fill", HOT),
    "notifications": ("bell", WHITE), "notifications_active": ("bell-fill", SKY),
    "notification_important": ("bell-fill", HOT), "speed+": ("speedometer2", WHITE),
    "speed-": ("speedometer", WHITE), "motor-off": ("slash-circle", WHITE),
    "cw": ("arrow-clockwise", WHITE), "ccw": ("arrow-counterclockwise", WHITE),
    "backspace": ("backspace", WHITE), "shuffle": ("shuffle", WHITE), "fine-tune": ("sliders", WHITE),
    "custom-script": ("code-square", WHITE), "hashtag": ("hash", WHITE), "spool": ("disc", WHITE),
}

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(IMG)
os.makedirs(os.path.join(OUT, "fonts"))

# 1. Start from material-dark artwork for every name KlipperScreen uses
src_imgs = os.path.join(FORK, "styles", "material-dark", "images")
for f in os.listdir(src_imgs):
    shutil.copy(os.path.join(src_imgs, f), IMG)

# 2. Overlay Bootstrap icons (recoloured: GdkPixbuf can't resolve currentColor)
bi = zipfile.ZipFile(os.path.join(VENDOR, "bi.zip"))
names = {os.path.basename(n)[:-4]: n for n in bi.namelist() if n.endswith(".svg")}
missing = []
for ks, (bname, colour) in MAP.items():
    if bname not in names:
        missing.append(bname)
        continue
    svg = bi.read(names[bname]).decode()
    svg = svg.replace("currentColor", colour)
    svg = re.sub(r'\sclass="[^"]*"', "", svg)
    for old in (os.path.join(IMG, ks + ".png"), os.path.join(IMG, ks + ".svg")):
        if os.path.exists(old):
            os.remove(old)
    open(os.path.join(IMG, ks + ".svg"), "w", encoding="utf-8", newline="\n").write(
        "<!-- STARSTACK-ADDED: Bootstrap Icons '%s' (MIT), colour %s -->\n" % (bname, colour) + svg)
if missing:
    sys.exit("Bootstrap icons not found: %s" % missing)

# 2b. StarStack logo (logo2, brand sheet) for the "Starting printer" screen
shutil.copy(os.path.join(HERE, "..", "design", "brand", "logo2.png"), os.path.join(IMG, "starstack-logo.png"))

# 3. Fonts (static TTFs we use: Regular 400, SemiBold 600, ExtraBold 800, Black 900)
ps = zipfile.ZipFile(os.path.join(VENDOR, "ps.zip"))
for w in ("Regular", "SemiBold", "ExtraBold", "Black"):
    n = "fonts/ttf/PublicSans-%s.ttf" % w
    open(os.path.join(OUT, "fonts", os.path.basename(n)), "wb").write(ps.read(n))
lic = [n for n in ps.namelist() if os.path.basename(n).upper() in ("LICENSE.MD", "LICENSE", "OFL.TXT", "LICENSE.TXT")]
if lic:
    open(os.path.join(OUT, "fonts", "OFL.txt"), "wb").write(ps.read(lic[0]))

# 4. CSS + conf from the klipper-ui repo (single source of truth)
shutil.copy(os.path.join(HERE, "..", "klipperscreen", "style.css"), os.path.join(OUT, "style.css"))
json.dump({"graph_colors": {
    "extruder": {"colors": ["FF8904", "FF6467", "F59E0B"], "state": 0},
    "bed": {"colors": ["00ACC7"], "state": 0},
    "fan": {"colors": ["88D8F2", "8FA0B8"], "state": 0},
    "sensor": {"colors": ["8FA0B8", "5CA300", "91C5FF", "1F3FAD"], "state": 0}}},
    open(os.path.join(OUT, "style.conf"), "w", newline="\n"), indent=4)

open(os.path.join(OUT, "LICENSES.md"), "w", encoding="utf-8", newline="\n").write(
    "# STARSTACK-ADDED: third-party assets in this theme\n\n"
    "- `images/` icons marked `STARSTACK-ADDED`: [Bootstrap Icons](https://github.com/twbs/icons) v1.13.1, MIT licence.\n"
    "- Other `images/`: copied from KlipperScreen `styles/material-dark` (same licence as KlipperScreen).\n"
    "- `fonts/`: [Public Sans](https://github.com/uswds/public-sans) v2.001, SIL Open Font License 1.1 (`fonts/OFL.txt`).\n")
print("theme built:", OUT, "| icons replaced:", len(MAP), "| total images:", len(os.listdir(IMG)))
