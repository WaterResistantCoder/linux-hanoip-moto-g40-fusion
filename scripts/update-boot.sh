#!/usr/bin/env bash
#
# Flash a boot image to the phone's boot_a partition from inside postmarketOS
# (over the USB ssh link) and reboot into it. Hands-free kernel iteration:
# no fastboot, no button combo.
#
#   scripts/update-boot.sh out/boot-hanoip-xyz.img
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
IMG="${1:?usage: update-boot.sh <boot.img>}"
KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
	-o BatchMode=yes -o ConnectTimeout=6 root@172.16.42.1)

echo ">> uploading $(basename "$IMG") ($(du -h "$IMG" | cut -f1))"
"${SSH[@]}" 'cat > /tmp/boot.img' < "$IMG"

# Write to both slots: the active slot has moved between boots (a failed boot
# flips ABL to the other slot), and the boot image is identical either way.
echo ">> writing to boot_a and boot_b"
"${SSH[@]}" 'for p in boot_a boot_b; do echo -n "$p: "; dd if=/tmp/boot.img of=/dev/disk/by-partlabel/$p bs=4M conv=fsync 2>&1 | tail -1; done; rm -f /tmp/boot.img'

echo ">> rebooting"
"${SSH[@]}" 'reboot' >/dev/null 2>&1 || true

echo ">> waiting for postmarketOS to come back"
for i in $(seq 1 30); do
	sleep 5
	if "${SSH[@]}" true 2>/dev/null; then
		echo ">> back up after $((i * 5))s"
		exit 0
	fi
done
echo ">> device did not come back"; exit 1
