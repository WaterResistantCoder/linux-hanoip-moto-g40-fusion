# hanoip port — working notes

Target: mainline Linux (`sm7150-mainline/linux`, branch **v7.2**) + postmarketOS on the
Moto G40 Fusion (hanoip, SM7150-AC). Milestone 0: **boot to a simple-framebuffer console**.

## Layout

```
dts/sm7150-motorola-common.dtsi   # SM7150 board common (from sm7150-xiaomi-common.dtsi, trimmed)
dts/sm7150-motorola-hanoip.dts    # hanoip device tree
scripts/setup-env.sh              # one-off: Docker volume + clone + toolchain
scripts/build-kernel.sh           # sync DTS -> build Image.gz + dtb -> out/
scripts/mkbootimg.sh              # header-v3 boot image -> out/boot-hanoip-*.img
scripts/init                      # minimal bring-up initramfs /init
scripts/vendor/                   # AOSP mkbootimg + pmOS kernel config
out/                              # build artifacts
```

## Build environment (macOS host, colima/Docker)

The kernel tree lives in a case-sensitive Docker volume (`hanoip-kernel`) and is built
natively inside an arm64 Debian container (`hanoip-build`); our DTS files stay in this
repo and are copied in at build time.

```
scripts/setup-env.sh          # once
scripts/build-kernel.sh       # Image.gz + sm7150-motorola-hanoip.dtb -> out/
scripts/mkbootimg.sh          # out/boot-hanoip-append.img (header v3)
```

## Flash / boot

```
# phone: Power + Volume Down -> fastboot
fastboot boot out/boot-hanoip-append.img
```

If ABL ignores the appended DTB, retry with the DTB in the boot image field:

```
DTB_MODE=field scripts/mkbootimg.sh
fastboot boot out/boot-hanoip-field.img
```

`fastboot flash userdata` is refused by design, so the rootfs (later) is written to UFS
**LUN 1** (`/dev/sdb`) from Linux itself, not via fastboot.

## hanoip-specific decisions

- **Panel**: Ilitek ILI7807S 1080x2460, DSC video mode. `simple-framebuffer` takes the
  bootloader splash at `0x9c000000`; `mdss_dsi0` is intentionally left **disabled** for
  milestone 0 so nothing resets the panel ABL left running.
- **Touch**: Ilitek ILI7807 TDDI on **GENI SE6** (`spi6 @ 0xa80000`), qup10 on gpio59-62
  (so those pins are **not** reserved, unlike surya). reset `tlmm8`, IRQ `tlmm9`.
  No mainline SPI/TDDI driver yet — the node is present but `disabled`.
- **UFS**: reset `tlmm119`, `vcc = l19a`, `vccq2 = l12a`; userdata on LUN 1.
- **Backlight**: `pm6150l_wled` (same as surya).
- **Panel control**: reset `pm6150l gpio9`, TE `tlmm10`, EN `tlmm55`.

## Upstream state (2026)

- `drivers/gpu/drm/panel/panel-ilitek-ili7807s.c` exists upstream (DLC DLC0697, video,
  non-DSC) but is **not** in sm7150 v7.2 — cherry-pick + add hanoip DSC timings later.
- No mainline Ilitek **SPI/TDDI** touch driver — port the downstream `tchip,ilitek` driver.
