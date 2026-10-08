#!/usr/bin/env python3
"""CI check for macros/*.cfg: parses like Klipper and compiles every gcode template with Klipper's
Jinja settings ('{' '}' expressions, '{% %}' blocks), checks variable_* values are valid literals,
and enforces the safety rules from docs/macro-safety-review.md (no limit/protection overrides).
Macro names in macros/*.cfg and config/*/printer.cfg must be names Klipper can call: a name like
_S1_PAUSE (letters, then a digit, not plain G-code like M600) is read as command "_S1" (D-089)."""
import ast
import configparser
import glob
import os
import re
import sys

import jinja2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = jinja2.Environment("{%", "%}", "{", "}")          # same delimiters as Klipper
FORBIDDEN = re.compile(r"^\s*(SET_HEATER_TEMPERATURE\s+.*TARGET=\s*[3-9]\d\d|FORCE_MOVE|SET_KINEMATIC_POSITION|"
                       r"SET_STEPPER_ENABLE|SET_VELOCITY_LIMIT|M109|M190|TEMPERATURE_WAIT)", re.I | re.M)
TRADITIONAL = re.compile(r"^[A-Z]\d+(\.\d+)?$")    # G28, M600, T0: Klipper's classic G-code
MISREAD = re.compile(r"^[A-Z_]+\d")                 # letters then a digit: Klipper splits it there
errors = []


def check_name(name, sec):
    """Klipper parses a command line as letters + number (G-code style) when it can."""
    macro = sec.split(None, 1)[1].upper()
    if not TRADITIONAL.match(macro) and MISREAD.match(macro):
        cut = MISREAD.match(macro).group(0)
        errors.append(f"{name} [{sec}]: Klipper reads this name as command \"{cut}\": rename it")


for path in sorted(glob.glob(os.path.join(ROOT, "config", "*", "printer.cfg"))):
    name = os.path.relpath(path, ROOT)
    cp = configparser.RawConfigParser(strict=False, inline_comment_prefixes=(";", "#"))
    with open(path, encoding="utf-8") as f:
        text = "".join(ln for ln in f if not ln.startswith("#*#"))   # SAVE_CONFIG block
    try:
        cp.read_string(text, source=name)
    except configparser.Error as e:
        errors.append(f"{name}: parse error: {e}")
        continue
    macros = [sec for sec in cp.sections() if sec.startswith("gcode_macro ")]
    for sec in macros:
        check_name(name, sec)
    print(f"{name}: {len(macros)} macro names checked")

for path in sorted(glob.glob(os.path.join(ROOT, "macros", "*.cfg"))):
    name = os.path.relpath(path, ROOT)
    cp = configparser.RawConfigParser(strict=False, inline_comment_prefixes=(";", "#"))
    try:
        cp.read_string(open(path, encoding="utf-8").read(), source=name)
    except configparser.Error as e:
        errors.append(f"{name}: parse error: {e}")
        continue
    for sec in cp.sections():
        if not sec.startswith(("gcode_macro ", "delayed_gcode ")):
            continue
        if sec.startswith("gcode_macro "):
            check_name(name, sec)
        for key, value in cp.items(sec):
            if key.startswith("variable_"):
                try:
                    ast.literal_eval(value)
                except (ValueError, SyntaxError) as e:
                    errors.append(f"{name} [{sec}] {key}: not a valid literal ({e})")
        gcode = cp.get(sec, "gcode", fallback="")
        try:
            ENV.from_string(gcode)
        except jinja2.TemplateSyntaxError as e:
            errors.append(f"{name} [{sec}] gcode line {e.lineno}: {e.message}")
        bad = FORBIDDEN.search(gcode)
        if bad:
            errors.append(f"{name} [{sec}]: forbidden command (safety review): {bad.group(1).strip()}")
    print(f"{name}: {len([s for s in cp.sections() if s.startswith('gcode_macro')])} macros checked")

if errors:
    print("\n".join("ERROR " + e for e in errors))
    sys.exit(1)
print("macros OK")
