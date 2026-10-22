# Deploying config and macros to the Pi

Every step needs the user's OK first (D-003). Show each SSH command and its reply in chat.

## Talking to the Pi
- `scripts/pi.sh '<command>'` runs one command over SSH with the project key and logs command and reply to
  `logs/ssh-<date>.log` (git-ignored). Use it for everything, including Moonraker calls
  (`curl -s localhost:7125/...`).
- Commands that need sudo: give the user the exact command to run themselves. Claude never types or sees
  a password (D-007, D-008).
- Screenshots of the touchscreen: `scripts/ks-screenshot.sh <file.png>`.

## Before
1. `print_stats.state` must not be `printing` or `paused` if the step restarts Klipper, Moonraker or the
   touchscreen. Macros only reload with a Klipper restart, so a macro fix waits for the print to end.
2. Back up what you replace on the Pi as `<file>.pre-dNNN` (example: `printer.cfg.pre-d089`) and say so in
   the build/deploy log.

## Deploy
- Macros, theme and installer files: `scripts/pi-install.sh --branch dev` (updates `~/klipper-ui` and runs
  `install.sh`; add `--dry-run` first when the installer itself changed). `install.sh` steps that need
  sudo (USB import, boot screen, fast boot, update helper) only take effect when the user runs it.
- `printer.cfg`: copy `config/s1/printer.cfg` over `~/printer_data/config/printer.cfg` (never a link),
  keeping any `#*# <---- SAVE_CONFIG ---->` block the Pi has.
- Touchscreen builds: `scripts/ks-update.sh --branch dev|bench` (fork repo, see its `fork-workflow` skill).

## After
1. Restart Klipper (`FIRMWARE_RESTART` or Mainsail) and read `/printer/info`: state `ready`, no warnings.
2. Read the end of `~/printer_data/logs/klippy.log` for errors.
3. Run the relevant checks from `docs/test-checklist.md` and record them as a new Run.
4. Leave the Pi on the branch the user expects. Mainsail shows "not on the primary branch" while a
   repo is on `dev`, so say when it needs switching back.
