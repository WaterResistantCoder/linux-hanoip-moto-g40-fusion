#!/usr/bin/env bash
#
# Bring up the host side of the hanoip USB network.
#
# The device is 172.16.42.1 on usb0 (CDC-ECM gadget). macOS shows it as an
# "en*" interface with 100baseTX media; we give the host 172.16.42.2.
#
# Setting an IP needs admin, so this uses a GUI password prompt (no password in
# the shell). Pass the interface as the first argument if it is not en8.
#
#   scripts/host-usb-net.sh [en8]
#
set -euo pipefail
IFACE="${1:-en8}"

osascript -e "do shell script \"ifconfig $IFACE 172.16.42.2 netmask 255.255.255.0 up\" with administrator privileges"
ifconfig "$IFACE" | grep "inet " || true
echo ">> device: ssh -i ~/.ssh/id_ed25519 root@172.16.42.1   (or scripts/dev-console.py)"
