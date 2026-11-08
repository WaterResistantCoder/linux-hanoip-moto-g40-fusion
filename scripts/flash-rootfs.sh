#!/usr/bin/env bash
#
# Write the postmarketOS rootfs image onto the hanoip userdata partition
# (UFS LUN 1, /dev/block/sdb24) through TWRP.
#
# `fastboot flash userdata` is refused by Moto ABL, so we boot TWRP (which has
# a working UFS driver) and stream the image onto the partition over adb.
#
#   scripts/flash-rootfs.sh [rootfs.img.xz]
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
FB="${FASTBOOT:-$HOME/Library/Android/sdk/platform-tools/fastboot}"
ADB="${ADB:-$HOME/Library/Android/sdk/platform-tools/adb}"
TWRP="${TWRP:-$HOME/ios-hanoip/twrp-hanoip.img}"
IMG="${1:-$HERE/out/rootfs-hanoip.img.xz}"

echo ">> fastboot devices:"; "$FB" devices || true
if "$FB" devices 2>/dev/null | grep -qw fastboot; then
	echo ">> booting TWRP ($TWRP)"
	"$FB" boot "$TWRP" | tail -1
fi

echo ">> waiting for adb (TWRP)..."
for i in $(seq 1 24); do
	"$ADB" devices | grep -qw recovery && break
	sleep 5
done
"$ADB" devices

echo ">> streaming $IMG -> /dev/block/sdb24"
# TWRP's dd cannot read stdin ("Bad address"); cat > works fine.
xz -dc "$IMG" | "$ADB" shell 'cat > /dev/block/sdb24'

echo ">> verifying"
"$ADB" shell 'blkid /dev/block/sdb24' || true
"$ADB" shell 'dd if=/dev/block/sdb24 bs=1024 count=1 2>/dev/null | od -An -tx1 -N 8' || true
echo ">> done. Reboot to fastboot and: fastboot boot out/boot-hanoip-rootfs.img"
