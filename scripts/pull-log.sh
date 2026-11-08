#!/usr/bin/env bash
#
# Wait for fastboot, boot TWRP, then pull the hanoip boot log that /init wrote to
# the last 1 MiB of the userdata partition (UFS LUN 1).
#
#   scripts/pull-log.sh
#
set -uo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
FB="${FASTBOOT:-$HOME/Library/Android/sdk/platform-tools/fastboot}"
ADB="${ADB:-$HOME/Library/Android/sdk/platform-tools/adb}"
TWRP="${TWRP:-$HOME/ios-hanoip/twrp-hanoip.img}"
OUT="${1:-$HERE/out/hanoip.log}"
TIMEOUT="${TIMEOUT:-1800}"

echo ">> waiting for fastboot..."
start=$(date +%s)
while ! "$FB" devices 2>/dev/null | grep -qw fastboot; do
	[ $(( $(date +%s) - start )) -ge "$TIMEOUT" ] && { echo "timeout"; exit 1; }
	sleep 3
done

echo ">> booting TWRP ($TWRP)"
"$FB" boot "$TWRP" || { echo "fastboot boot twrp failed"; exit 1; }

echo ">> waiting for adb (TWRP)..."
"$ADB" wait-for-device
# give TWRP a moment to bring up adbd
sleep 8
"$ADB" devices

echo ">> reading the log from userdata (sdb24, last 1 MiB)"
"$ADB" shell 'S=$(cat /sys/class/block/sdb24/size); \
	dd if=/dev/block/sdb24 bs=1024 skip=$(( (S*512-1048576)/1024 )) count=1024 2>/dev/null' \
	> "$OUT"

# trim trailing NULs
python3 - "$OUT" <<'PY'
import sys
d = open(sys.argv[1], "rb").read().split(b"\x00", 1)[0]
open(sys.argv[1], "wb").write(d)
print("log bytes:", len(d))
PY
echo ">> log at $OUT"
head -50 "$OUT"
