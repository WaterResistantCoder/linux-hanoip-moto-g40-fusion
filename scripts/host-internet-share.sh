#!/usr/bin/env bash
#
# Share the Mac's internet with the phone over the hanoip USB link.
#
# The phone is 172.16.42.1 on usb0; macOS shows the link as an "en*" interface
# with 172.16.42.2. This enables IP forwarding and adds a NAT rule (in a pf
# anchor, so the rest of the system's pf config is untouched), then prints the
# commands to run on the phone.
#
#   scripts/host-internet-share.sh [wan-if] [lan-if]
#
# Defaults: wan = the current default-route interface, lan = en8.
#
set -euo pipefail

WAN="${1:-$(route -n get default 2>/dev/null | awk '/interface:/{print $2}')}"
LAN="${2:-en8}"
SUBNET="172.16.42.0/24"
ANCHOR="com.apple/hanoip"
CONF="/tmp/hanoip-pf.conf"

echo ">> WAN = $WAN   LAN = $LAN   subnet = $SUBNET"

printf 'nat on %s from %s to any -> (%s)\n' "$WAN" "$SUBNET" "$WAN" > "$CONF"
cat "$CONF"

osascript -e "do shell script \"sysctl -w net.inet.ip.forwarding=1 >/dev/null; pfctl -a ${ANCHOR} -f ${CONF}; pfctl -E\" with administrator privileges"

echo ">> pf NAT rules now active:"
sudo -n pfctl -a "$ANCHOR" -s nat 2>/dev/null || true

cat <<EOF

>> On the phone:
   ip route add default via 172.16.42.2
   printf 'nameserver 1.1.1.1\\nnameserver 8.8.8.8\\n' > /etc/resolv.conf
   ping -c1 1.1.1.1

   scripts/host-internet-share.sh  (no args re-runs with the same defaults)
EOF
