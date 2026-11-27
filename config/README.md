# Printer configs

| Folder | What | Use on |
|---|---|---|
| `s1/` | **StarStack S1, production standard**: `printer.cfg` (FLY Micro4, sensorless X/Y, E3D PZ probe, Revo Voron 40 W, Galileo 2; D-081, D-084, D-089), a reference copy of its `moonraker.conf`, its board firmware build settings (`micro4-firmware.config`, `firmware.conf`, used by the update helper, D-087) and its OrcaSlicer start G-code (`orca-start-gcode.txt`, D-089) | The S1 only. Copy `printer.cfg` to `~/printer_data/config/` (it is not linked: Klipper writes PID and mesh results into it) |
| `s1-proto/` | The **old prototype S1**'s `printer.cfg` (v1.7: v1.6 split, D-NEW shared config) and `firmware.conf` (uses `s1/micro4-firmware.config`). Orca profile shared with `s1/` | The prototype only, printer type `s1-proto` |
| `s1_common.cfg` | **Everything every S1 shares** (motion, currents, probe, heaters, fans, homing and print macros). Linked by `install.sh` as `starstack_s1_common.cfg`, so it changes with every klipper-ui update; each S1 `printer.cfg` includes it and sets only its own values (serial, motor ports, travel, z_offset, sensorless thresholds, mesh area, park, brush, homing spot). Never put a value SAVE_CONFIG writes here | Every S1 |
| | **Printer type**: `install.sh --printer=s1` or `--printer=s1-proto` stores it in `/var/lib/starstack/printer`; `deploy-cfg.sh` only puts `config/<type>/printer.cfg` on that Pi (bench: no type) | |
| `bench/` | Bench `printer.cfg` v2.2: fake heaters on logic pins, fake homing, nothing wired (D-027) | A bare board on the bench. **Never on a real printer** |

Board firmware for the S1's FLY Micro4 goes through its Katapult bootloader, built with the 16 KiB
offset (D-083):

```bash
cd ~/klipper && make menuconfig     # RP2040, Bootloader offset: 16KiB bootloader, USB
make clean && make
# stop Klipper first (Mainsail › power menu › Service Control › klipper › Stop), then:
~/klippy-env/bin/python ~/katapult/scripts/flashtool.py -d /dev/serial/by-id/usb-Klipper_rp2040_E6647C7403679636-if00 -f out/klipper.bin
```

Start Klipper again afterwards. (If the board is already in Katapult, use `-d /dev/serial/by-id/usb-katapult_rp2040_MELLOW-if00`.)
