# Linux on the Moto G40 Fusion (hanoip) — mainline port

Running an **actual Linux OS** (mainline kernel + postmarketOS/Alpine + Plasma Mobile) on the
**Motorola Moto G40 Fusion / G60** (codename **hanoip**, SM7150-AC / Snapdragon 732G) — **not** an
Android ROM. This repo is the full record of the port: device tree, panel/touch drivers, build and
flash scripts, and a detailed handoff of every fix.

Based on the [`sm7150-mainline`](https://github.com/sm7150-mainline) kernel (**v7.2**).

## Status

| | |
| --- | --- |
| Boot to userspace | ✅ |
| Panel (DSI, DRM) | ✅ ILI7807S 1080×2460 |
| Touch | ✅ ILITEK ILI7807 TDDI (mainline `ilitek-ipio` driver + stock firmware) |
| GPU | ✅ Adreno 618 (`gpu-initialized: 1`) |
| USB networking | ✅ (`usb0` = 172.16.42.1, SSH) |
| **Plasma Mobile** | ✅ KWin/Wayland, full app set, wallpapers |
| WiFi | ⚠️ WCN3990 — driver + firmware + power-up done; **blocked on the missing SM7150 WPSS** |
| Modem / calls | ❌ not started |

## Read this

- **[HANDOFF.md](HANDOFF.md)** — the complete record: every milestone, every bug, every fix, the
  build/flash workflow, and how to resume. **Start here.**
- **[TOUCH-FOR-IOS.md](TOUCH-FOR-IOS.md)** — self-contained touch bring-up findings (the wrong
  firmware was the root cause) written for a parallel iOS port.
- `hw/` — captured hardware description from the stock phone (`hanoip.dts`, TWRP `dmesg`, iomem).
- `dts/` — the hanoip device tree + ILI7807S panel driver.
- `scripts/` — setup, build, mkbootimg, flash, update-boot, serial console, host USB-net, and the
  kernel patches (`kernel-patches/`).

## Quick build & boot

```sh
scripts/setup-env.sh        # Docker build container + kernel volume + toolchain (once)
scripts/build-kernel.sh     # Image.gz + DTB -> out/  (DTB is built into the kernel)
# header-v3 boot image (ABL ignores the appended DTB; we build the DTB in):
mkbootimg.py --header_version 3 --pagesize 4096 \
    --kernel arch/arm64/boot/Image.gz --ramdisk empty.cpio.gz \
    --cmdline "console=tty0 console=ttyMSM0,115200 earlycon rootwait"
scripts/update-boot.sh out/<img>   # flashes boot_a over SSH and reboots
```

## The three "gotchas" that cost the most time

1. **ABL passes its own DTB** and ignores the boot image's — so the DTB is compiled **into** the
   kernel (`scripts/kernel-patches/force-builtin-dtb.py`) and `__fdt_pointer` is repointed.
2. **`sm7150.dtsi` has no RAM size** (the bootloader was expected to fill it); with a built-in DTB
   you must set it yourself.
3. **Touch failed for months on the wrong firmware** — the generic `FW_TDDI_TRUNK_FB` vs the stock
   `FW_ILITEK_TDDI_TM.bin`. See `TOUCH-FOR-IOS.md`.

Everything else — panel clocks, USB peripheral mode, the GPU split-ZAP firmware, Plasma Mobile's
libinput/udev trap, the OpenRC runlevel quirks — is in **[HANDOFF.md](HANDOFF.md)**.
