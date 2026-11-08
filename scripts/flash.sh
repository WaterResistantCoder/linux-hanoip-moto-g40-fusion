#!/usr/bin/env bash
#
# Temporarily boot a hanoip boot image (Power + Volume Down -> fastboot first).
#
#   scripts/flash.sh [out/boot-hanoip-append.img]
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
FASTBOOT="${FASTBOOT:-$HOME/Library/Android/sdk/platform-tools/fastboot}"
IMG="${1:-$HERE/out/boot-hanoip-append.img}"

[ -x "$FASTBOOT" ] || { echo "fastboot not found at $FASTBOOT (set FASTBOOT=)"; exit 1; }
[ -f "$IMG" ] || { echo "boot image not found: $IMG"; exit 1; }

echo ">> devices:"
"$FASTBOOT" devices
echo ">> booting $IMG (temporary; does not flash)"
"$FASTBOOT" boot "$IMG"
