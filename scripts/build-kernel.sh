#!/usr/bin/env bash
#
# Build the hanoip mainline kernel + DTB inside the Docker build container.
#
# Prereqs (one-off):
#   docker volume create hanoip-kernel
#   docker run -d --name hanoip-build -v hanoip-kernel:/kernel -v "$PWD":/host \
#       -w /kernel debian:bookworm sleep infinity
#   # then clone sm7150-mainline/linux v7.2 into the volume and install deps
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
CONT="${CONT:-hanoip-build}"
TREE="${TREE:-/kernel}"
QCOM="$TREE/arch/arm64/boot/dts/qcom"
DTB="sm7150-motorola-hanoip.dtb"

echo ">> syncing device trees into $QCOM"
docker exec "$CONT" bash -c "
set -e
cp /host/dts/sm7150-motorola-common.dtsi /host/dts/sm7150-motorola-hanoip.dts $QCOM/
grep -q '$DTB' $QCOM/Makefile || \
  sed -i '/sm7150-xiaomi-tucana.dtb/a dtb-\$(CONFIG_ARCH_QCOM)\t+= $DTB' $QCOM/Makefile
"

echo ">> building Image.gz + dtbs"
docker exec "$CONT" bash -c "cd $TREE && make ARCH=arm64 -j\$(nproc) Image.gz dtbs"

echo ">> copying artifacts to $HERE/out"
mkdir -p "$HERE/out"
docker cp "$CONT:$TREE/arch/arm64/boot/Image.gz" "$HERE/out/Image.gz"
docker cp "$CONT:$QCOM/$DTB" "$HERE/out/$DTB"
ls -la "$HERE/out/"
