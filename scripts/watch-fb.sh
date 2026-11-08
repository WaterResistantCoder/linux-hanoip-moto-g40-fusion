#!/usr/bin/env bash
#
# Wait until the phone shows up in fastboot, then boot the given image.
# So the user only has to bring the phone to fastboot.
#
#   scripts/watch-fb.sh out/boot-hanoip-xxx.img
#
set -uo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
FB="${FASTBOOT:-$HOME/Library/Android/sdk/platform-tools/fastboot}"
IMG="${1:-$HERE/out/boot-hanoip-current.img}"
TIMEOUT="${TIMEOUT:-1800}"

[ -f "$IMG" ] || { echo "image not found: $IMG"; exit 1; }
echo ">> watching for fastboot, then booting $(basename "$IMG") (timeout ${TIMEOUT}s)"

start=$(date +%s)
while :; do
	if "$FB" devices 2>/dev/null | grep -qw fastboot; then
		echo ">> device in fastboot — booting"
		"$FB" boot "$IMG" && { echo ">> boot sent"; exit 0; }
		echo ">> fastboot boot failed; still watching"
	fi
	now=$(date +%s)
	[ $((now - start)) -ge "$TIMEOUT" ] && { echo ">> timed out waiting for fastboot"; exit 1; }
	sleep 3
done
