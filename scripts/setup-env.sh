#!/usr/bin/env bash
#
# One-off setup of the hanoip kernel build environment.
# Creates a case-sensitive Docker volume, clones sm7150-mainline/linux v7.2,
# and starts a persistent build container with the toolchain installed.
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
CONT="${CONT:-hanoip-build}"
VOL="${VOL:-hanoip-kernel}"
BRANCH="${BRANCH:-v7.2}"
REPO="${REPO:-https://github.com/sm7150-mainline/linux}"

echo ">> volume: $VOL"
docker volume create "$VOL" >/dev/null

echo ">> starting build container: $CONT"
docker rm -f "$CONT" >/dev/null 2>&1 || true
docker run -d --name "$CONT" -v "$VOL":/kernel -v "$HERE":/host -w /kernel \
  debian:bookworm sleep infinity >/dev/null

echo ">> installing toolchain"
docker exec "$CONT" bash -c '
  set -e
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq build-essential bc bison flex libssl-dev libelf-dev \
    python3 perl cpio rsync git curl ca-certificates kmod busybox-static \
    device-tree-compiler >/dev/null
'

echo ">> cloning $REPO ($BRANCH)"
docker exec "$CONT" bash -c "
  set -e
  if [ ! -d /kernel/.git ]; then
    git clone --depth 1 -b $BRANCH $REPO /kernel
  fi
"

echo ">> vendoring mkbootimg"
docker cp "$HERE/scripts/vendor/mkbootimg.py" "$CONT:/kernel/mkbootimg.py" 2>/dev/null || true
docker exec "$CONT" bash -c 'mkdir -p /kernel/gki && touch /kernel/gki/__init__.py'
docker cp "$HERE/scripts/vendor/generate_gki_certificate.py" \
  "$CONT:/kernel/gki/generate_gki_certificate.py" 2>/dev/null || true

echo ">> fetching the pmOS kernel config as .config"
docker cp "$HERE/scripts/vendor/config-postmarketos-qcom-sm7150.aarch64" \
  "$CONT:/kernel/.config" 2>/dev/null || \
  echo "   (config not vendored; fetch manually)"

docker exec "$CONT" bash -c 'cd /kernel && make ARCH=arm64 olddefconfig >/dev/null'

echo
echo "Environment ready. Build with: scripts/build-kernel.sh"
