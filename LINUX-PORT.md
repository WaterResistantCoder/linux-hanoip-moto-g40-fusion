# Running a real Linux (not Android) on the Moto G40 Fusion (hanoip)

Research 2026-11-08. Goal: an actual Linux OS on the device, not a ROM on top of Android.

## Short answer
Yes — there is a mature **mainline-Linux + postmarketOS** effort for the **Qualcomm SM7150**
(the Snapdragon 730/730G/732G). hanoip is **not yet a supported device**, but it is the **same
SoC family** as several supported phones and a port is very feasible. The one head start we have:
the hanoip device tree already captured in `hw/hanoip.dts` / `hw/hanoip-fdt.dtb`.

## The project: `sm7150-mainline`
- GitHub org: https://github.com/sm7150-mainline  (Matrix: `#sm7150-mainline:matrix.org`)
- **linux**  — WIP mainline kernel for SM7150 (fork of torvalds/linux): https://gitlab.com/sm7150-mainline/linux
- **u-boot** — SM7150 U-Boot (used to boot, chain-loaded).
- **pmaports** — postmarketOS device/kernel packages (incl. a *generic* `qcom-sm7150` package).
- **nightly-builds** — weekly postmarketOS edge images (boot.img + rootfs) for supported devices.
- **firmware-*** — nonfree firmware blobs (adreno, wcnss/ath10k Wi-Fi, etc.) per device.
- Upstreaming is in progress: a ~33-patch "Add support for Qualcomm Snapdragon SM7150 SoC and
  Google Pixel 4a" series is on LKML.

## Devices already supported (downstream-fdt + nightly builds)
| Device | Codename |
|---|---|
| Xiaomi POCO X3 / X3 NFC | surya / karna |
| Xiaomi Redmi Note 10 Pro | sweet |
| Xiaomi Redmi Note 12 Pro 4G | sweet_k6a |
| Xiaomi Mi 9T / Redmi K20 | davinci |
| Xiaomi Mi Note 10 / CC9 Pro | tucana |
| Xiaomi Mi Note 10 Lite | toco |
| Xiaomi Mi 11 Lite | courbet |
| Xiaomi POCO X2 / Redmi K30 4G | phoenix |
| Google Pixel 4a | sunfish |
| Samsung Galaxy A71 | SM-A715F |

Reported status for the closest device (surya): "basically everything works" on the generic
`qcom-sm7150` package (the only known wart is the touchscreen in the initramfs).

## What a hanoip port needs
1. **Device tree** for hanoip (`msm-…/hanoip.dts` + `hanoip-*.dtsi`) derived from our captured
   `hw/hanoip.dts` — UFS on LUN 1, 1080x2460 ILI7807S panel, Ilitek ILI7807 SPI touch, pm6150/pm6150l.
2. **postmarketOS device package** (`device-motorola-hanoip`): deviceinfo, kernel cmdline, firmware
   deps; model it on `device-xiaomi-surya` / `device-xiaomi-sweet`.
3. **Kernel** from `sm7150-mainline/linux` (config `qcom_defconfig`-ish) + the hanoip DTS.
4. **Firmware blobs** from the stock phone (`/vendor/firmware_mnt`): adreno, wcnss, etc.
5. **Flashing**: U-Boot + boot.img + rootfs. Bootloader is already unlocked; ABL uses **boot image
   header v3** and `fastboot boot` works (same as the iOS work).

## Caveats (and a nice overlap)
- The hard parts are the **panel (ILI7807S DSI)** and the **Ilitek ILI7807 SPI touch** — the very
  same components that are hard in the iOS port. Mainline has no SPI Ilitek TDDI driver; the panel
  needs a `panel-ili7807`-style DRM driver. Everything else (CPU, UFS, USB, PMIC, GPU, Wi-Fi) is
  shared with the supported devices and should come up.
- No hanoip port exists in the sm7150-mainline tree (checked `downstream-fdt` and `nightly-builds`);
  we would be first, but on well-trodden ground.

## Alternatives (also "real Linux", less mainline)
- **Droidian** / **Ubuntu Touch** — Debian/Ubuntu userspace, usually on a downstream Android kernel.
- **postmarketOS downstream** — pmOS on the LineageOS kernel.
These boot more easily but are "Linux on an Android kernel", not what was asked.

## Next steps if we pursue this
1. Clone `sm7150-mainline/linux`; add a minimal `hanoip` DTS (start from `surya`/`sweet`, swap the
   panel + touch + UFS LUN) and get it to **boot to a serial/display console**.
2. Build a postmarketOS `device-motorola-hanoip` package; use a supported device's nightly image as
   a template for the rootfs.
3. Bring up display (simple-framebuffer first), then USB, then the panel/touch drivers.
