#!/usr/bin/env bash
#
# Build a header-v3 boot image for hanoip from the built kernel + initramfs.
#
# DTB_MODE=append  (default)  cat Image.gz + dtb, no --dtb  (surya's recipe)
# DTB_MODE=field              --kernel Image.gz --dtb dtb   (boot image dtb field)
# DTB_MODE=raw                cat Image (uncompressed) + dtb, no --dtb
# DTB_MODE=none               --kernel Image.gz only (DTB built into the kernel)
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
CONT="${CONT:-hanoip-build}"
TREE="${TREE:-/kernel}"
QCOM="$TREE/arch/arm64/boot/dts/qcom"
DTB="sm7150-motorola-hanoip.dtb"
DTB_MODE="${DTB_MODE:-append}"
CMDLINE="${CMDLINE:-console=ttyMSM0,115200 earlycon rootwait}"
OUT="$HERE/out/boot-hanoip-${DTB_MODE}.img"

echo ">> building initramfs"
docker exec "$CONT" bash -c '
set -e
rm -rf /tmp/initramfs && mkdir -p /tmp/initramfs/bin /tmp/initramfs/proc /tmp/initramfs/sys /tmp/initramfs/dev /tmp/initramfs/mnt
cp /bin/busybox /tmp/initramfs/bin/busybox
for a in sh mount umount cat echo ls dmesg grep sleep poweroff reboot tail; do ln -sf busybox /tmp/initramfs/bin/$a; done
cp /host/scripts/init /tmp/initramfs/init
chmod +x /tmp/initramfs/init
cd /tmp/initramfs && find . | cpio -o -H newc 2>/dev/null | gzip -9 > /kernel/initramfs.cpio.gz
'

echo ">> building boot image (DTB_MODE=$DTB_MODE, header v3)"
if [ "$DTB_MODE" = "none" ]; then
  KARG="--kernel arch/arm64/boot/Image.gz"
elif [ "$DTB_MODE" = "field" ]; then
  KARG="--kernel arch/arm64/boot/Image.gz --dtb arch/arm64/boot/dts/qcom/$DTB"
elif [ "$DTB_MODE" = "raw" ]; then
  docker exec "$CONT" bash -c "cd $TREE && cat arch/arm64/boot/Image arch/arm64/boot/dts/qcom/$DTB > Image-dtb"
  KARG="--kernel Image-dtb"
else
  docker exec "$CONT" bash -c "cd $TREE && cat arch/arm64/boot/Image.gz arch/arm64/boot/dts/qcom/$DTB > Image.gz-dtb"
  KARG="--kernel Image.gz-dtb"
fi

docker exec "$CONT" bash -c "
set -e
cd $TREE
python3 mkbootimg.py \
  --header_version 3 \
  --pagesize 4096 \
  $KARG \
  --ramdisk initramfs.cpio.gz \
  --cmdline '$CMDLINE' \
  --os_version 12.0.0 --os_patch_level 2024-01 \
  -o /kernel/boot-hanoip.img
"

docker cp "$CONT:$TREE/boot-hanoip.img" "$OUT"
ls -la "$OUT"
echo
echo "Flash test:  fastboot boot $OUT"
