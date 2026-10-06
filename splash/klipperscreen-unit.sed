# STARSTACK (D-069): applied by install.sh to /etc/systemd/system/KlipperScreen.service
# (backup: KlipperScreen.service.pre-starstack). Starts the touchscreen app as soon as the
# system is up instead of after the network and Moonraker: it shows its own "Starting printer"
# screen and connects when Moonraker is ready (it already does this after every restart).
/^After=systemd-user-sessions.service plymouth-quit-wait.service$/{
i\
# StarStack (D-069): plymouth-quit-wait removed (it waits for the network)
s/ plymouth-quit-wait.service//
}
/^After=moonraker.service$/{
i\
# StarStack (D-069): no longer waits for Moonraker
s/^/#/
}
