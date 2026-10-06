# STARSTACK (D-075): applied by install.sh to /etc/systemd/system/klipper.service and
# moonraker.service (backups: *.pre-starstack). Klipper and Moonraker start without waiting
# ~7 s for Ethernet/Wi-Fi to connect: Klipper talks to the board over USB/serial, and Moonraker
# listens on 0.0.0.0, so Mainsail works as soon as the network comes up. Without a network at
# all (e.g. Wi-Fi not set up yet) the printer no longer waits for the network timeout either.
/^Requires=network-online.target$/{
i\
# StarStack (D-075): Wants instead of Requires, no longer started after the network
s/^Requires=/Wants=/
}
/^After=network-online.target$/{
i\
# StarStack (D-075): starts without waiting for the network
s/^/#/
}
