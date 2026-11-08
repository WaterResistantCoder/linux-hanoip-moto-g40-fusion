# hanoip-linux — a real Linux on the Moto G40 Fusion

Goal: run an **actual Linux OS** (mainline kernel + postmarketOS) on this phone — **not** an
Android-based ROM. This folder is a fresh, self-contained start for that.

## What's here
- `LINUX-PORT.md` — the research: the `sm7150-mainline` project, supported devices, what a hanoip
  port needs, caveats.
- `hw/` — captured hardware description from the stock phone:
  - `hanoip.dts` / `hanoip-fdt.dtb` — the **live device tree** (the key asset for writing a DTS).
  - `dmesg-twrp.txt` — the stock kernel's boot log (working drivers, addresses, panel/touch init).
  - `cmdline.txt`, `partitions-proc.txt`, `meminfo.txt`, `iomem.txt`.

## Device facts (verified)
- Moto G40 Fusion / G60, codename **hanoip**, XT2147-1, carrier **retin**. Bootloader **unlocked**.
- SoC **SM7150-AC / Snapdragon 732G** (`sdmmagpie`), Adreno 618, **4 GB** RAM, UFS 2.1.
- Display **1080x2460** IPS, panel **ILI7807S** (DSI video mode).
- **UFS: `userdata` is on LUN 1 (`sdb`)**, logical block size **4096**.
- Touch: **ILITEK ILI7807 TDDI**, on **GENI SE6 (`0xa80000`, wrapper1 SE0) SPI**; reset **TLMM
  gpio8**, IRQ **TLMM gpio9**; pin roles **miso=gpio59, mosi=gpio60, clk=gpio61, cs=gpio62**.
  Powered by the DSI panel rails (VDDI = `pm6150_l13` = RPMh `ldoa13`).
- Buttons: power via PM6150 PON (`kpdpwr`); volume-up via `gpio-keys`; assist via TLMM GPIO 58.
- Bootloader **Moto ABL**, A/B slots; **boot image must be header v3**; `fastboot boot` works,
  `fastboot flash userdata` is refused by design.

## The platform to build on
- `github.com/sm7150-mainline` — mainline kernel (`gitlab.com/sm7150-mainline/linux`), U-Boot,
  postmarketOS `pmaports` (generic `qcom-sm7150`), weekly nightly images, per-device firmware.
- Closest supported devices: **surya** (POCO X3 NFC), **sweet** (Redmi Note 10 Pro),
  **davinci**, **sunfish** (Pixel 4a). hanoip is not supported yet.

## Next steps
1. Clone `sm7150-mainline/linux`; add a minimal `hanoip` DTS from `hw/hanoip.dts` (start from
   surya/sweet, swap panel + touch + UFS LUN 1). Boot to a simple-framebuffer console.
2. Create a postmarketOS `device-motorola-hanoip` package from a supported device's package.
3. Bring up display, then USB, then the panel (ILI7807S DRM) and touch (Ilitek SPI) drivers.

## Phone ops
- Fastboot: **Power + Volume Down**.
- Temporary recovery: `fastboot boot twrp-hanoip.img` (keep a copy handy).
- The iOS/XNU port work lives in `~/ios-hanoip` (see its `HANDOFF.md`); this folder is unrelated to it.
