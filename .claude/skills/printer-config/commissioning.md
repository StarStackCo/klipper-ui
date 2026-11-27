# Commissioning a printer (staged power-up)

How the S1 was brought up in Phase 3.5 (PLAN, D-081 to D-084, test-checklist Run 7). Use it for a new
unit, a replaced board, or rewiring. Each stage needs the user's OK before the next one.

1. **Config review before power.** Pins, thermistor types, heater pins, steppers, probe and homing checked
   against the hardware and the board's docs. `min_temp` 0 on nozzle and bed, so an unplugged sensor stops
   the printer (D-081). Macro safety review updated.
2. **Board firmware matches the host's Klipper.** On a unit installed with `install.sh --printer=s1` the
   update helper does it by itself once Klipper has seen the board, even when Klipper then shuts down on an
   unplugged sensor, or when the board waits in Katapult (D-NEW first boot). By hand: build with the
   Katapult 16 KiB offset and flash with `flashtool.py` (D-083, `config/README.md`). The standard config
   finds the board by its Pi USB port (`/dev/serial/by-path/...`, D-NEW port path): plug the Micro4 into
   the same port on every unit. A board **without Katapult** (the helper reports it; the RP2040 shows as
   `2e8a:0003`) needs Katapult put on once through its BOOT button: steps not written yet (B-NEW katapult setup).
3. **Klipper connects, no errors.** Unplugged sensors must stop it with "ADC out of range".
4. **Heaters at low targets.** Bed and hotend to about 40 to 60 °C; watch that they reach and hold the
   target with no heater check errors. Fans spin.
5. **Motors.** `STEPPER_BUZZ` for the right axis and direction (needs `[force_move]`, off again
   afterwards). Then sensorless homing of X and Y one axis at a time, ready to press STOP.
6. **Probe and Z.** Probe reads open at rest and triggers on touch; Z homing; extrusion by hand.
7. **First print**, then PID tune nozzle and bed at print temperatures and copy the `SAVE_CONFIG` values
   into the repo (D-084).
8. **UI checks**: the touchscreen walk-through and the full test checklist.

Before a unit ships to a customer, also do the open items in BACKLOG B-13 (image, per-unit setup, network
access rules, v1.0.0).
