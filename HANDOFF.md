# hanoip Linux port — handoff

Mainline Linux (`sm7150-mainline/linux`, branch **v7.2**) on the **Moto G40 Fusion / G60** (hanoip,
SM7150-AC). **The phone runs Plasma Mobile with working touch, GPU and USB networking; only WiFi
(WCN3990) is unfinished** — see MILESTONE 7.

Milestones reached: **0** console on panel · **1** postmarketOS rootfs on UFS · **2** panel DRM ·
**4** touch · **5** GPU · **6** Plasma Mobile · **7** WiFi (blocked on the missing SM7150 WPSS).

## How to build & boot

```
scripts/setup-env.sh        # once: Docker volume + clone + toolchain
scripts/build-kernel.sh     # Image.gz + dtb -> out/
scripts/mkbootimg.sh        # -> out/boot-hanoip-append.img
# or the current hand-built image:
fastboot boot out/boot-hanoip-current.img
```

Recovery if it hangs: hold **Power ~15 s**, then **Power + Volume Down** for fastboot.

## What works

- `fastboot boot` of a **header-v3** boot image works.
- The kernel blob must carry the **arm64 Image header** (magic `ARM\x64`) or ABL ignores it
  (a 28-byte bare payload did nothing; adding the header made it run).
- The kernel boots through `setup_arch` → `paging_init` → all initcall levels → `kernel_init`
  (proven by checkpoints and by a deliberate `emergency_restart()` at `kernel_init`).
- The panel stays lit (no blanking) with `clk_ignore_unused pd_ignore_unused`.

## The three bugs found (all fixed in the DTS / boot path)

1. **ABL passes its own DTB.** It hands the kernel the *stock downstream* hanoip DTB in x0 and
   ignores the boot image's DTB (appended or `--dtb`). Mainline arm64 does no machine matching,
   so the kernel booted with the wrong tree (no `simple-framebuffer`). Fix:
   `scripts/kernel-patches/force-builtin-dtb.py` — compiles our DTB into the kernel and points
   `__fdt_pointer` at it in `setup_arch()`.
2. **Memory size zero.** `sm7150.dtsi` says *"We expect the bootloader to fill in the size"*
   (`reg = <0 0x80000000 0 0x0>`). With the built-in DTB, ABL can't patch it, so the kernel saw
   zero RAM and panicked in `map_mem()`. Fix: `&{/memory@80000000} { reg = <0 0x80000000 0 0xfdd00000>; }`.
3. **Display clocks gated.** With `mdss` disabled nothing claims the DSI/DPU clocks, so
   `clk_disable_unused` gated them and blanked the panel right after the colours. Fix:
   `clk_ignore_unused pd_ignore_unused` in the DTB `bootargs`.

Also fixed: the hanoip TZ/`removed` carve-out is `0x4100000`, larger than the shared sm7150
value `0x2d00000` — override `&tz_mem`.

## MILESTONE 0 REACHED

**A console is on the panel.** The last blocker was the display clock controller: with
`mdss` disabled nothing claims the DSI/DPU clocks, so the kernel gated them and blanked the
panel. Disabling the display clock controller in the DTS keeps the bootloader's display alive:

```dts
&dispcc {
	status = "disabled";
};
```

Together with `clk_ignore_unused pd_ignore_unused` in the bootargs, the panel now stays on and
`fbcon` shows the kernel log.


### Update — console + userspace working

- `CONFIG_DEVTMPFS_MOUNT=y` so `/dev/console` exists before `/init`.
- The initramfs `/init` must stay alive (a bare `busybox sh` gets EOF on stdin and
  exits -> `Kernel panic - not syncing: Attempted to kill init!`). Keep PID 1 in a loop.
- Working image: `out/boot-hanoip-alive2.img` (console shows the kernel log, UFS up,
  `/init` runs and stays). Driver `sync_state() pending due to ...` lines are harmless.
- Latest clean kernel patch set = `force-builtin-dtb.py` only; the checkpoint/debug
  patches have been reverted from the tree.

Next: postmarketOS `device-motorola-hanoip` + rootfs on UFS LUN 1, then panel DRM + touch.

## MILESTONE 1 — postmarketOS rootfs on UFS LUN 1

The rootfs is written to the phone's internal storage and the kernel switches into it.

**How it is built** (all in the Docker container, no pmbootstrap):

- `apk.static` (Alpine aarch64) installs a real postmarketOS rootfs into a directory:
  `alpine-base postmarketos-base` from Alpine edge + the postmarketOS (Nura) repo
  (`https://mirror.postmarketos.org/postmarketos/master`, which redirects to
  `mirror.nura.eco/postmarketos/main`). ~72 MiB / 139 packages, OpenRC init.
- Configured: hostname `hanoip`, root password `147147`, and
  `/etc/local.d/hanoip-banner.start` prints a banner once userspace is up.
- Packed with `mke2fs -t ext4 -d <dir> -L pmOS_root` into a 2 GiB image, xz-compressed
  to ~19 MiB (mostly empty), at `out/rootfs-hanoip.img.xz`.

**How it gets on the device:**

- `fastboot flash userdata` is refused by ABL, so `scripts/flash-rootfs.sh` boots TWRP and
  streams the image over adb onto `/dev/block/sdb24` (UFS LUN 1 userdata):
  `xz -dc rootfs.img.xz | adb shell 'cat > /dev/block/sdb24'`
  (TWRP's `dd` cannot read stdin — use `cat >`).

**How it boots:**

- Kernel bootargs (in the DTB, since ABL's cmdline is ignored) now include
  `root=/dev/sdb24 rootfstype=ext4 rootwait rw`.
- The initramfs (`scripts/init-rootfs`) waits for `/dev/sdb24`, mounts it, moves
  proc/sys/dev and `switch_root`s into `/sbin/init`. `CONFIG_SCSI_UFS_QCOM` and
  `CONFIG_EXT4_FS` are built-in, so this needs no modules.
- Working image: `out/boot-hanoip-rootfs.img`.

`fastboot boot out/boot-hanoip-rootfs.img` boots postmarketOS from internal storage.

**Result: the panel shows `Welcome to Nura!` (postmarketOS) with a `hanoip login:` prompt on
tty1** — a real Linux userspace running from the phone's internal storage. Milestone 1 reached.

Next: get an interactive channel (USB gadget console/network — there is no working touch or
keyboard yet, so the login prompt cannot be typed into), then panel DRM + touch.

## USB network (interactive channel)

There is no touch/keyboard yet, so USB is the way in.

- The kernel already has DWC3 + configfs gadget + CDC-ECM/ACM/RNDIS built in, and the DTS
  enables `&usb_1`. But `usb_1_dwc3` was `dr_mode = "otg"` behind a role switch that needs the
  PM6150 TypeC driver (a module we do not have), so it never enumerated. Fix: `dr_mode =
  "peripheral"` in `sm7150-motorola-common.dtsi`.
- pmOS builds its USB gadget in *its* initramfs; ours does not, so `scripts/init-rootfs` now
  creates the CDC-ECM gadget via configfs, binds the UDC, and (as a fallback) starts a busybox
  `telnetd` on usb0.
- macOS speaks CDC-ECM natively and shows the phone as a new `en*` interface. Device is
  `172.16.42.1`, host `172.16.42.2`. A DHCP server (`unudhcpd`, with `/etc/conf.d/unudhcpd`
  pinned to `172.16.42.1`/`172.16.42.2`) is enabled for auto-config; if it does not come up,
  set the host side by hand: `sudo ifconfig en8 172.16.42.2 netmask 255.255.255.0 up`.
- `openssh-server` is **not** pulled in by `postmarketos-base` (only the client), so the rootfs
  build adds it explicitly, sets `PermitRootLogin yes`, and embeds an ssh public key
  (`SSH_PUBKEY`, default `~/.ssh/id_ed25519.pub`) for root and user. Passwords are `147147`.

Diagnostics: `scripts/init-rootfs` writes USB state to `/root/hanoip-usb.txt` on the rootfs
(read it back by mounting `sdb24` in TWRP).

### MILESTONE 2 — interactive access

**`ssh root@172.16.42.1` works over the USB cable** (key from `SSH_PUBKEY`, or password
`147147`). The gadget also exposes a CDC-ACM serial port (`/dev/tty.usbmodemhanoip1` on
macOS) with a getty on `ttyGS0`; `scripts/dev-console.py` drives it:

```
ssh -i ~/.ssh/id_ed25519 root@172.16.42.1 'uname -a'
python3 scripts/dev-console.py 'dmesg | tail'
```

Device: `usb0 = 172.16.42.1/24`, host side `172.16.42.2/24`. `unudhcpd.usb0` serves DHCP;
if macOS does not pick it up, set the host IP by hand (`sudo ifconfig en8 172.16.42.2
netmask 255.255.255.0 up`). The device is stable (`sshd`, `unudhcpd` up; root is
`/dev/sdb24` ext4 rw).

Gotcha found here: `postmarketos-base` pulls only the openssh **client**; the rootfs build
must add `openssh-server` explicitly (pmbootstrap does this unless `--no-sshd`).

The busybox `telnetd` fallback (port 23) turned out unreliable; the ACM serial console is the
dependable fallback.

## MILESTONE 3 — panel DRM (ILI7807S)

The display is now driven by mainline MSM DRM, not the bootloader's simple-framebuffer.

- The panel driver was generated from the stock DTB with `linux-mdss-dsi-panel-driver-generator`
  (`panel-gen/` here) and lives at `drivers/gpu/drm/panel/panel-tm-ili7807s-678.c`
  (Kconfig `DRM_PANEL_TM_ILI7807S_678`). 1080x2460 video mode, 4 lanes, DSC.
- `dts/sm7150-motorola-hanoip.dts`: `&mdss`, `&mdss_dsi0` (with `panel@0`), `&mdss_dsi0_out`
  and `&mdss_dsi0_phy` enabled; the old `&dispcc { status = "disabled" }` hack is gone.
- Required config fixes: `CONFIG_REGULATOR_QCOM_REFGEN=y` (the DSI host/PHY need the refgen
  supply or they defer-probe forever) and `CONFIG_BACKLIGHT_QCOM_WLED=y`.
- Result: `[drm] Initialized msm`, `msmdrmfb` replaces simpledrm, connector `card1-DSI-1`
  is `connected`, mode `1080x2460`, fbcon on the panel. The probe-time
  `DSI PLL(0) lock failed` is benign — the PLL locks on the real modeset.
- Backlight: `&pm6150l_wled` now has `status = "okay"`, so the WLED driver binds and
  `/sys/class/backlight/backlight` exists (max 4095) — brightness is kernel-controlled.
- Remaining for the display: the Adreno GPU firmware (`a630_sqe.fw`/`a630_gmu.bin`) is not on
  the rootfs, so only the display pipeline (not 3D accel) is up. The GPU needs firmware blobs
  from the stock phone.

## MILESTONE 4 (WIP) — touch (Ilitek ILI7807 TDDI, SPI)

Goal: the Ilitek ILI7807 TDDI touch, on GENI SE6 (`spi6 @ 0xa80000`), reset TLMM 8,
IRQ TLMM 9, I/O rail pm6150 l13. Mainline has no Ilitek SPI/TDDI driver.

Base driver: **`hychiang73/ipio_touch_driver`** (ILITEK's official TDDI driver). It already
targets our chip (`CHIP_TYPE_ILI7807`), `SPI_INTERFACE`, and has a `PT_QCOM` path whose DT
name is `tchip,ilitek`. Clone lives at `$TMP/opencode/ipio` (host) and `/root/ipio` (container).

**The driver now builds and BINDS, and the chip is detected.** Working boot image:
`out/boot-hanoip-touch2.img` (HOST_DOWNLOAD disabled) / `out/boot-hanoip-touch.img`.

### What was fixed to make it build (all in `/kernel/drivers/input/touchscreen/ilitek-ipio/`)

- `platform.c`: deleted the legacy suspend/fb-notifier block (`tpd_suspend`/`tpd_resume`/
  `ilitek_platform_notifier_fb`/early-suspend), `ilitek_platform_reg_suspend()` -> `return 0`;
  gpiod for reset/irq (`devm_gpiod_get`, `gpiod_set_value`, `gpiod_to_irq`); `free_irq(..., NULL)`;
  fixed raw newlines left inside `ipio_err(...)` strings; removed an unused `out:` label.
- `core/firmware.c`, `core/parser.c`, `core/mp_test.c`, `platform.c`: `set_fs`/`mm_segment_t`/
  `get_ds`/`KERNEL_DS` + `vfs_read`/`vfs_write` -> `kernel_read`/`kernel_write`;
  `strncpy` -> `strscpy`; `f_dentry` -> `file_inode(f)`;
  `getnstimeofday`/`rtc_time_to_tm` -> `ktime_get_real_ts64`/`rtc_time64_to_tm`;
  `f->f_op->llseek/read` -> `kernel_read`.
- `core/spi.c`: `spi->master` -> `spi->controller`. **Added `ipio_spi_write_then_read()`** and use
  it instead of the kernel's `spi_write_then_read` (which rejects >`SPI_BUFSIZ`/32-byte transfers
  with -EAGAIN; errors are swallowed while `do_reset` is set). It builds an `spi_message` over the
  DMA-safe `dma_txbuf`/`dma_rxbuf`.
- `userspace.c` was **missing** from the tree (it defines `netlink_reply_msg`, `katoi`,
  `ilitek_proc_init/remove`) — copied in and added to the Makefile. Then: `/proc`
  `struct file_operations` -> `struct proc_ops` (`proc_read/write/ioctl`), `dev_mkdir` via
  `start_creating_path()`/`vfs_mkdir(..., &nop_mnt_idmap, ..., &delegated_inode)`/`end_creating_path()`
  (this tree's VFS differs), legacy `gpio_*` -> `gpiod_*`, and fixed `copy_to_user(apk, sizeof(apk)*100)`
  and `copy_from_user(..., size - 1)` underflow.
- `common.h`: `MIN`/`MAX` guarded with `#ifndef`.

### DTS (`dts/sm7150-motorola-hanoip.dts`)

`&spi6` child `touchscreen@0` is now `status = "okay"`, adds `irq-gpios = <&tlmm 9 ...>`.
**Critical:** with `cs-gpios` present the CS pin must be muxed as **gpio**
(`pinctrl-0 = <&qup_spi6_spi>, <&qup_spi6_cs_gpio>`), not `qup_spi6_cs` — otherwise the controller
claims gpio62 and the `cs-gpios` request fails, taking the whole SPI probe down with -EINVAL.

Also: `CONFIG_SPI_QCOM_GENI=y` (was `=m`, so the bus never probed) and
`CONFIG_TOUCHSCREEN_ILITEK_IPIO=y` in `/kernel/.config` (edited in the container; the vendored
config in `scripts/vendor/` is stale and not the source of truth).

### What works now (verified on the phone)

- `spi6.0` bound to `ILITEK_TDDI`; `core_config_get_chip_id`: `PID = 0x78071c03`, `ID = 0x7807`.
- IRQ registered (irq 142, `ilitek`), `ILITEK_TDDI` input device created.
- ICE-mode **register reads AND writes work** (proven live through
  `/proc/ilitek/read_write_register`: `echo "0x1,0x1,0x41016,0x0,0x1" > ...` then read back).
  NOTE: the proc write handler drops the last byte, so use `echo` (trailing newline), not `printf`.

## MILESTONE 4 REACHED — TOUCH WORKS (2026-11-08)

**Root cause: the wrong firmware.** The vendor driver's built-in `FW_TDDI_TRUNK_FB.ili` is a
generic/trunk image that this chip will not run. The correct firmware is the stock Moto file
**`FW_ILITEK_TDDI_TM.bin`** (Intel HEX text, 358761 bytes), found at `/firmware/` in the stock
`vendor` partition (extracted from `super`, extent 4, `debugfs`).

With it, the driver comes up cleanly at boot:

```
AP CRC is Correct ! (fea9bcbd) : (fea9bcbd)     (DATA ca3e7527, TUNING 94d9c4dd)
nStartAddr = 0x000000, nEndAddr = 0x01F200, block_number(AF) = 4
Procotol Version = 5.6.0      Core Version = 4.6.210.0
Panel info: width = 1080, height = 2460
input resolution : max_x = 1080, max_y = 2460, min_x = 0, min_y = 0
input: ILITEK_TDDI as /devices/platform/soc@0/ac0000.geniqup/a80000.spi/spi_master/spi6/spi6.0/input/input2
```

Working image: `out/boot-hanoip-touch9.img`. The firmware is copied to `out/FW_ILITEK_TDDI_TM.hex`.

### What was actually wrong (in order of discovery)

1. **Wrong firmware** (the real root cause). The chip refuses to run the trunk image, so nothing
   answered in AP mode. Fixed by embedding the stock HEX: `core/FW_ILITEK_TDDI_TM.hex` +
   `core/fw_hex.S` (incbin) + `core/fw_hex.o` in the Makefile, and `fw_upgrade_file_convert()`
   falling back to `convert_hex_file(ipio_stock_fw_hex, ...)` instead of `convert_ili_file()`.
2. **DMA CRC check polled the wrong bit.** The stock (`calc_hw_dma_crc`) polls **BIT1** of
   `0x048006` (`busy & 0x02`), DMA dest `0x0002725C`, stop `0x02000000`, clr-int `0x2`, plus a
   DMA reset via `0x40040 = 0x00800000` then `0x0`. We were polling BIT0 and reading `0x02`
   (= done) as "busy", so every download looked corrupt.
3. **AP-mode SPI framing was wrong.** Stock: read = `0x83` + `n_rx + 2` bytes, **ACK `0xA3` at
   `rx[1]`, payload at `rx[3]`**; write = `0x82, len_hi, len_lo, data`. (`SPI_ACK` added to
   `core/spi.h`.)
4. **Sensing was never enabled.** With the correct FW the driver read valid `0x5a` demo packets but
   every one had all-`0xff` fingers (no touch). Adding `core_config_sense_ctrl(true)` after the FW
   upgrade (→ `core_protocol_func_control(0, 1)`, func `sense_ctrl`) made the FW actually sense.

All four are in the tree now. Verified end-to-end from `/dev/input/event2`:

```
KEY BTN_TOUCH 1 / ABS MT_TRACKING_ID / ABS MT_POSITION_X / ABS MT_POSITION_Y / BTN_TOOL_FINGER
t=126.541637  x=300 y=2081  ->  299/2080 -> 295/2078 -> 293/2076 ...   (tracks a drag)
```

Gotcha for reading the events by hand: on 64-bit arm64 `sizeof(struct input_event)` is **24**
bytes, so `dd if=/dev/input/event2 bs=16` fails with EINVAL — use a multiple of 24.

### Finishing touches

- **Logging quieted.** `ipio_debug_level` defaulted to `DEBUG_ALL`, so every report dumped the whole
  packet. It is now `DEBUG_NONE`; raise it at runtime via `/proc/ilitek/debug_level`. The idle
  all-`0xff` packet also tripped the checksum path every report — that (and the parse failure) is now
  `ipio_debug`, not `ipio_err`. `dmesg` went from thousands of lines to ~740.
- **Self-contained firmware.** The driver prefers `/sdcard/ILITEK_FW` if present and otherwise uses
  the built-in stock HEX (`Open hex file fail, using built-in stock firmware`), so nothing has to be
  dropped on the rootfs.
- Working image: **`out/boot-hanoip-touch11.img`** (also `out/boot-hanoip-touch-working.img`).

### Also done this session

- **Weston installed on the phone** (`weston`, `weston-terminal`, `font-dejavu` + 67 deps), fetched
  in the build container and installed offline — so a graphical UI is possible now.
- **Phone internet:** the Mac's Zscaler agent RSTs *forwarded* traffic, so NAT does not give the
  phone internet even though forwarding and the NAT rule work (the phone can ping the LAN router but
  not the internet). Packages therefore have to be fetched in the container and copied over.
- **WiFi is NOT up.** `wifi@18800000` (`qcom,wcn3990-wifi`) is `okay` in the DT and the WCN3990
  firmware is in the vendor partition, but `CONFIG_ATH10K_SNOC=m` is not on the rootfs, there is no
  WPSS/WCSS remoteproc node, and the 5 WiFi regulators are not modelled. That is a bring-up task of
  the same shape as touch was. The stock driver source used as the reference lives in
`~/ios-hanoip/ilitek/` (`ilitek_v3_mmi`).

### Original analysis (kept for context)

The host download itself is byte-perfect: reading IRAM over ICE mode via
`/proc/ilitek/read_write_register` returns exactly `CTPM_FW[]`. The ICE-mode register path always
worked; the failures were all in AP mode.

What fails is the **MCU never starts / never answers in FW mode**:

- `core_spi_ice_mode_enable()` (the FW-mode handshake: send `0x82`, expect `0xA3`) returns
  `0x82` -- i.e. MISO echoes the command, the chip is not driving it. Every FW-mode read/write
  then fails with `Failed to write data, -2` (`CHECK_RECOVER`), so no protocol/FW/tp/key version
  is read (`input resolution : max_x = 0, max_y = 0`) and finger-report reads fail.
- This is identical with `HOST_DOWNLOAD` on (download path) and off (flash path; flash read also
  returns `M_ID = ff, DEV_ID = ffff`), and **also when the download is re-triggered at runtime**
  with the panel fully up (`cat /proc/ilitek/fw_upgrade`) -- so the TDDI display/panel reset is
  not wiping it.
- The vendor's own DMA CRC verification never completes either: `host_download_dma_check()` polls
  bit0 of `0x048006` and always reads `0x02` (`BIT0 is busy`), so the CRC compare is `calc vs
  (ffffffff)` (the `ffffffff` is just its `-1` return).

Net: data is in IRAM, the ICE-mode hardware path works, but the MCU/FW-mode SPI does not come up.
The missing piece is chip-specific (the MCU boot/run sequence, or a register value the vendor
driver gets from somewhere we don't have). Needs the vendor's ILI7807 docs, or a known-good
ILI7807 SPI port, to compare against -- blind iteration has hit diminishing returns.

**Debug aids currently left in the tree** (revert when done):
- `core/firmware.c`: CRC mismatch made **non-fatal** (test only, logs instead of failing), and the
  DMA check now logs the real `0x048006` value.
- `core/spi.c`: `ipio_spi_write_then_read()` now does a **single full-duplex transfer** (command +
  dummy in one burst); the two-transfer split gave the same `0x82` result.

### Next steps (need external info)

1. Get the vendor's ILI7807 (or ILI9881) SPI register/boot documentation, or the stock kernel's
   touch driver, and compare the MCU-start sequence (`0x40040 = 0xAE` "code reset", `0x40050`
   reset key `0x19878`, the `0x048006` DMA-int bit, `0x042c34` SPI speed-up).
2. Ask in #sm7150-mainline / postmarketOS whether anyone has this TDDI touch up on mainline.
3. Cheap things not yet tried: SPI mode 3, lower SPI clock, `ENABLE_SPI_SPEED_UP` off, a longer
   post-download settle delay before the first FW-mode access.

### Gotchas hit along the way

- `scripts/update-boot.sh` used to write only `boot_a`, but the active A/B slot had moved to
  `boot_b` (a failed boot flips ABL), so flashes went to the unused slot. It now writes **both**
  `boot_a` and `boot_b`.
- A build with `RST_METHODS = SW_RST` (no host download) hung the device into fastboot; recovered
  with `fastboot flash boot <good.img>` + `fastboot reboot`.
- The repetition-guard plugin (see `~/.config/opencode/`) false-positived on a long debug turn.

## PARKED ALTERNATIVE — headless "remote desktop" if touch is abandoned

Touch does **not** gate this. The phone already boots postmarketOS (Alpine) from UFS with SSH
over USB working, so it can be used as a headless Linux box driven from the work laptop:

1. **Remote display:** install a light desktop + a VNC server on the phone; connect from macOS
   **Screen Sharing** (built-in VNC client) -> a Linux desktop as a window on the Mac.
   (Alternatives: `xpra`, `noVNC`, `code-server`.)
2. **"A real distro":** pmOS is Alpine; for Debian/Ubuntu, `debootstrap` an arm64 chroot inside
   the rootfs and run the desktop from there (or replace the rootfs with a Debian arm64 image).
3. **WiFi (optional):** bring up WCN3990 (`ath10k_snoc`) so it is not USB-tethered -- needs the
   firmware blobs pulled from the stock `vendor` partition plus DTS/config. This is a second
   bring-up of similar shape to touch, but with a much better mainline track record.

Fastest path to a working result is USB-only (no WiFi bring-up). Internet for package installs
comes from macOS Internet Sharing over the USB link.

## MILESTONE 5 — GPU (Adreno 618) works

The Adreno 618 now initializes at boot:

```
gpu-initialized: 1
revision: 618 (06010800)
```

**Firmware** (all extracted from the stock phone; the vendor partition has SQE/GMU, the
**modem** partition has the ZAP):

| file | source | installed at |
| --- | --- | --- |
| `a630_sqe.fw` | `vendor` → `/firmware/` | `/lib/firmware/qcom/` |
| `a630_gmu.bin` | `vendor` → `/firmware/` | `/lib/firmware/qcom/` |
| `a615_zap.mdt` + `.b00/.b01/.b02` | `modem` → `/image/` | `/lib/firmware/qcom/sm7150/motorola/hanoip/` |

Two things had to be right:

1. **Timing** — the GPU probes at ~6 s, *before* the rootfs (with `/lib/firmware`) is mounted, so the
   firmware must be in the **built-in initramfs** (`/kernel/initramfs_src/lib/firmware/...`), which is
   the rootfs at that point. It is also on the real rootfs for runtime.
2. **Format** — the ZAP is qcom's **split** format. Concatenating `.mdt + .b00 + .b01 + .b02` into a
   `.mbn` looks like a valid ELF but is rejected: `qcom_scm_pas_init_image` returns `-EINVAL` because
   the hash must be the last thing in the file. Instead point the DT at the `.mdt`
   (`firmware-name = "qcom/sm7150/motorola/hanoip/a615_zap.mdt"`) and ship the `.b*` segments —
   `mdt_load_split_segment()` swaps the extension to `b00`/`b01`/… and loads them.

Notes: the GPU still logs `supply vdd/vddcx not found, using dummy regulator` — harmless, because
mainline models the CX/GX GDSCs as **power domains** (`gpu_cx_gdsc`/`gpu_gx_gdsc`), not regulators.
Also: **never** test the GPU by unbind/rebind at runtime — it hangs the display (SSH survives); always
reboot-test.

## MILESTONE 6 — Plasma Mobile (desktop-class UI)

The phone runs **Plasma Mobile** (KDE) on the panel, with working touch.

- **Session**: Alpine's `plasma-mobile` shell (`org.kde.plasma.mobileshell`) under `kwin_wayland`,
  started by OpenRC service `/etc/init.d/plasma-mobile` → launcher `/usr/local/bin/start-plasma-mobile`.
  KWin uses its **NoopSession** backend (opens `/dev/dri/card1` directly — no logind needed):
  `KWIN_DRM_DEVICES=/dev/dri/card1`, run as root. The `plasma.desktop` wayland-session entry runs
  the *desktop* shell; use `startplasmamobile` (sets `PLASMA_DEFAULT_SHELL=org.kde.plasma.mobileshell`).
- **Apps** (all from Alpine `edge/{main,community}`, fetched offline in the build container and
  installed from the on-device local repo):
  - *First batch*: `plasma-dialer` (Phone), `plasma-phonebook` (Contacts), `spacebar` (SMS),
    `plasma-camera`, `megapixels`, `kclock`, `kalk`, `kweather`, `qmlkonsole` (Terminal), `kcalc`,
    `krecorder`.
  - *Second batch*: `angelfish` (browser), `koko` (gallery), `neochat` (Matrix), `tokodon` (Mastodon),
    `kasts` (podcasts), `audiotube` (YouTube), `keysmith` (OTP), `calindori` (calendar),
    `itinerary` (travel), `dolphin` (files), `filelight` (disk usage), `kcharselect`.
  - *System integration*: `breeze` (style/cursor/colour scheme), `breeze-wallpapers`,
    `plasma-workspace-wallpapers`, `kscreen`, `powerdevil`, `polkit-kde-agent-1`, `bluedevil`,
    `modemmanager`, `udisks2`, `urfkill`, `geoclue`, `iio-sensor-proxy`, `callaudiod`.
  - `kaidan` (XMPP) has an unsatisfiable dep (`libQXmppQt6`) in Alpine and is not installable.
- **Wallpaper**: the homescreen (`org.kde.plasma.mobile.homescreen.folio`) uses
  `wallpaperplugin=org.kde.image`; set the image in
  `~/.config/plasma-org.kde.plasma.mobileshell-appletsrc` under
  `[Containments][1][Wallpaper][org.kde.image][General] Image=file:///usr/share/wallpapers/...`.
  (The `org.kde.image` provider logs "unknown wallpaper provider type / application/octet-stream"
  on some paths but the wallpaper applies.)
- **Touch in Plasma — the udev trap**: libinput's udev backend **ignores any input device that udev
  has not tagged `ID_INPUT`**. udev sets that from `/usr/lib/udev/rules.d/60-input-id.rules`, which
  comes from the **`eudev`** package. The rootfs had only `eudev-libs` (no rules, no `udevd`), so the
  ILITEK panel was never tagged and Plasma received no touch. Fix: install `eudev` + `kmod-libs` +
  `udev-init-scripts`, start `udevd`, trigger udev → `ILITEK_TDDI` gets `ID_INPUT_TOUCHSCREEN=1` and
  KWin opens `/dev/input/event2`.
- **Rootfs repair**: the rootfs had lost `apk-tools` and `openrc` (the `--force-broken-world`
  `openrc-user` → `openrc-user-pam` swap during the Plasma install removed them) and had **dangling
  runlevel symlinks** (`sshd`, `tmpfs`, `swapfile`, `postmarketos-zram-swap`, …) that made OpenRC
  abort the `default` runlevel, so *nothing* started on boot. Fixed by bootstrapping an aarch64
  `apk.static`, restoring `apk-tools`/`openrc`/`eudev` from a local repo (`/var/localrepo`), and
  deleting the dangling symlinks.

### Making the session start on boot (OpenRC quirks)

Getting Plasma to start on a cold boot took several fixes, all on the rootfs:

1. **Missing `openrc`/`apk-tools`** — the `--force-broken-world` `openrc-user` → `openrc-user-pam`
   swap during the Plasma install removed them. Restored from a local repo (below).
2. **Dangling runlevel symlinks** (`sshd`, `tmpfs`, `swapfile`, `postmarketos-zram-swap`, and the
   `systemd-*` ones) made OpenRC abort the `default` runlevel, so nothing started. Delete them.
3. **OpenRC silently skipped `dbus`/`plasma-mobile`** even with clean symlinks — the cached deptree
   (`/run/openrc/deptree`) didn't contain them (81 services, `grep dbus` → 0). `openrc default`
   wouldn't start them either. Worked around with a **`/etc/local.d/plasma.start`** script
   (the `local` service *is* started on boot):
   ```sh
   #!/bin/sh
   rc-service dbus start
   sleep 1
   rc-service plasma-mobile start
   ```
   `rc_depend_strict="NO"` was also set in `/etc/rc.conf` (belt and braces).
4. **Offline package management** — the phone has no internet, so a **local repo** lives at
   `/var/localrepo/aarch64` (`/etc/apk/repositories` = `/var/localrepo`). Rebuild its index with
   `apk index --allow-untrusted -o APKINDEX.tar.gz *.apk`. (Installing by file path also works.)

## MILESTONE 7 (WIP) — WiFi (WCN3990) — blocked

The WCN3990 WiFi is **very close** but not working. Everything up to the QMI handshake is done:

- **DT**: `&wifi` in `sm7150-motorola-common.dtsi` is enabled with all supplies and the **CXO
  reference clock** (`clocks = <&rpmhcc RPMH_RF_CLK2>, <&aoss_qmp>; clock-names = "cxo_ref_clk_pin",
  "qdss";`). The mainline sm7150 node had **no clocks** — without them the chip has no reference
  clock. The PMU regulators come from the `wcn3998-pmu` node (pwrseq).
- **Drivers** built **into** the kernel: `CFG80211`, `MAC80211`, `ATH10K`, `ATH10K_SNOC`,
  `POWER_SEQUENCING_QCOM_WCN`, `RFKILL` (all `=y`). To force `=y` you must also set
  **`CONFIG_RFKILL=y`** (else `depends on RFKILL || !RFKILL` evaluates to `m` and caps CFG80211 at
  `m`) and disable the Q6V5 chain (`QCOM_Q6V5_ADSP/MSS/PAS/WCSS`, `QCOM_Q6V5_COMMON`,
  `QCOM_RPROC_COMMON`) — otherwise `ATH10K_SNOC` is capped at `m` by
  `depends on QCOM_RPROC_COMMON || QCOM_RPROC_COMMON=n`.
- **Firmware**: the **mainline** WCN3990 firmware (from Alpine's `linux-firmware-ath10k`,
  `.zst`-decompressed — the kernel has no `FW_LOADER_COMPRESS`) at
  `/lib/firmware/ath10k/WCN3990/hw1.0/{firmware-5.bin,wlanmdsp.mbn,board-2.bin}`, on **both** the
  rootfs and the built-in initramfs. (The vendor partition only has WLAN config + `bdwlan.*`; the
  vendor `wlanmdsp.mbn` is in the **modem** partition if the mainline one doesn't match.)
- **Chip power-on** — required a **driver patch** (see below). With it, all six PMU regulators show
  `1` (enabled) and `rf_clk2` runs at 38.4 MHz.

**The blocker**: ath10k's QMI runs over **QRTR** (`AF_QIPCRTR` in `qmi.c`), and the WCN3990's QRTR
node is provided by a **WPSS / Q6V5 remoteproc** (as `sc7280-wpss-pas` does). Mainline has **no
`qcom,sm7150-wpss-pas`** compatible and **no WPSS node** in `sm7150.dtsi`, so nothing registers that
node → the WLFW QMI lookup never gets a reply → no wiphy, no `wlan0`.

**To finish WiFi** you'd add the SM7150 WPSS subsystem:
1. A WPSS remoteproc DT node (`qcom,sm7150-wpss-pas`) — regs/interrupts/clocks/power-domains. The
   stock tree uses Android's `icnss`, so there is **no wpss node to copy**; the register map must be
   derived (the wifi block is at `0x18800000`; the WCN3990's subsystem is around there).
2. A resource table in `drivers/remoteproc/qcom_q6v5_pas.c` (`ssr_name = "wpss"`, the PAS regions,
   `qcom_add_glink_subdev(..., "wpss")` so the QRTR node appears).
3. The **WPSS firmware** from the stock phone's `modem` partition (`wpss.mdt` + `.b*`).
4. Enable `QCOM_Q6V5_PAS` + `QCOM_Q6V5_COMMON` + `QCOM_RPROC_COMMON` (they may be modules — this is
   fine, `ATH10K_SNOC` only needs them present, not built-in, as long as they're `m` consistently).

### The WCN3990 power-on driver patch (NOT upstream)

`drivers/net/wireless/ath/ath10k/snoc.c` — the normal flow powers the chip **after** the QMI
handshake (`hif_power_up` ← `core_start` ← `core_register` ← FW_READY), but the chip's boot ROM
needs power **before** the QMI lookup. Patch `ath10k_snoc_probe` to power on first:

```c
	/* hanoip: power the WCN3990 before the QMI lookup so its boot ROM
	 * can answer; the normal flow only powers on after FW_READY. */
	ret = ath10k_hw_power_on(ar);
	if (ret) {
		ath10k_err(ar, "failed to power on: %d\n", ret);
		goto err_fw_deinit;
	}

	ret = ath10k_qmi_init(ar, msa_size);
```

With this the regulators + clock come up; the QMI handshake is still blocked by the missing WPSS.

## Hands-free iteration

`fastboot flash boot` put our kernel on `boot_a`, so a plain `reboot` returns to
postmarketOS. `scripts/update-boot.sh <boot.img>` uploads a new boot image over ssh, writes it
to `/dev/disk/by-partlabel/boot_a`, reboots and waits — no fastboot or button combo needed.
(`reboot bootloader` does not reach fastboot on this device.)

Note: the environment TLS is intercepted by a Zscaler proxy; the container needs the
Zscaler root CA (`update-ca-certificates`) before git/curl work.

## Where it stands now

The phone boots straight into **Plasma Mobile** on the panel, with working **touch**, **GPU**
(Adreno 618), **USB networking** and a full app set. The rootfs is `/dev/sdb24` (48 GB). OpenRC
starts `sshd`, `dbus`, `udev` and (via `/etc/local.d/plasma.start`) `plasma-mobile` on boot.

**Only WiFi is unfinished** — see MILESTONE 7. It needs the SM7150 WPSS remoteproc added (DT +
PAS resource + firmware); everything else on the WiFi path is done.

## Resuming in a new session (read this first)

The phone will be **wiped to iOS**, so this repo is the only record. To pick the port back up:

1. **Build env** — Docker container `hanoip-build` (Debian) with the `hanoip-kernel` volume at
   `/kernel` (the `sm7150-mainline/linux` **v7.2** tree) and this repo at `/host`.
   `scripts/setup-env.sh` recreates it. The container needs the Zscaler CA before git/curl work.
2. **Build + flash** — `scripts/build-kernel.sh` (builds `Image.gz` + DTB; it copies `dts/*` into
   the kernel tree and the DTB is built in via `force-builtin-dtb.py`), then
   `mkbootimg.py --header_version 3 --pagesize 4096 --kernel arch/arm64/boot/Image.gz
   --ramdisk empty.cpio.gz --cmdline "console=tty0 console=ttyMSM0,115200 earlycon rootwait"`, then
   `scripts/update-boot.sh out/<img>` (flashes `boot_a` over SSH + reboots).
3. **Access** — `ssh -i ~/.ssh/id_ed25519 root@172.16.42.1` (usb0). If the host's `en8` loses its
   address (it does on every USB reconnect), run `scripts/host-usb-net.sh` (macOS admin prompt).
   Serial fallback: `scripts/dev-console.py` (`/dev/tty.usbmodemhanoip3`).
4. **Rootfs** — postmarketOS/Alpine on `/dev/sdb24`; offline packages live in `/var/localrepo`.
   The `plasma-mobile` OpenRC service starts the session as root with KWin's NoopSession.
5. **WiFi** — continue MILESTONE 7 (add the WPSS). Don't forget the `ath10k_snoc` power-on patch.

**Boot image on the device now**: `out/boot-hanoip-wifi3.img` (GPU + split ZAP + boot-time `e2fsck`
+ built-in WiFi stack + the ath10k power-on patch). `out/boot-hanoip-fsck.img` is the previous good
one; `out/boot-hanoip-fallback.img` the one before that.

## Files

```
HANDOFF.md                        # this file — the full record
TOUCH-FOR-IOS.md                  # self-contained touch findings for the iOS port (also in ~/ios-hanoip)
dts/sm7150-motorola-common.dtsi   # SM7150 board common (WiFi node + CXO clock, PMU, USB, touch)
dts/sm7150-motorola-hanoip.dts    # hanoip: memory size, tz override, bootargs, GPU zap firmware-name
dts/panel-tm-ili7807s-678.c       # ILI7807S panel driver
scripts/                          # setup/build/mkbootimg/flash/update-boot/dev-console/host-usb-net + kernel-patches/
hw/                               # captured stock DTS/dmesg/partitions/iomem
out/                              # built boot images (see "Where it stands now")
pmaports/, panel-gen/             # earlier experiments
```

## Device facts (verified)

- SM7150-AC, 4 GB, UFS 2.1, `userdata` on **LUN 1** (`/dev/sdb`, 4096-byte blocks; rootfs = `sdb24`).
- Panel **Ilitek ILI7807S** 1080×2460 (DSC video); splash framebuffer at **`0x9c000000`**.
- Touch **Ilitek ILI7807 TDDI** on **GENI SE6** (`spi6 @ 0xa80000`), qup10 on gpio59-62,
  reset `tlmm8`, IRQ `tlmm9` (mainline driver in `drivers/input/touchscreen/ilitek-ipio/`).
- GPU **Adreno 618** (`a630_sqe.fw`, `a630_gmu.bin` from `vendor`; `a615_zap.mdt`+segments from `modem`).
- WiFi **WCN3990** at `0x18800000`; PMU regulators via the `wcn3998-pmu` pwrseq node.
- ABL: `fastboot boot` works, header v3, `fastboot flash userdata` refused by design.
- **A/B slots**: the bootloader marks a slot unbootable after ~7 boots if nothing sets the
  "successful" flag (Linux doesn't). If you get **"No bootable A/B slot"**, run
  `fastboot set_active a` (resets the retry count) and `fastboot flash boot out/<img>`.

## Debug patches currently applied to the kernel tree (NOT in this repo)

The kernel tree lives in the Docker volume `hanoip-kernel` (`/kernel`). Applied via
`scripts/kernel-patches/*.py`:

- `force-builtin-dtb.py` — **required** (see bug 1).
- `paint-head.py`, `paint-fb-diagnostic.py`, `paint-setup-big.py`, `paint-checkpoints.py`,
  `paint-late.py`, `paint-fine.py`, `paint-paging.py`, `paint-mapmem.py`, `paint-mapmem2.py`,
  `paint-late3.py`, `paint-simpledrm.py`, `paint-initcalls.py` — **debug checkpoints**, remove
  once the console works (each paints the top band a colour; see the checkpoint script comments).
- `reset-kernel-init.py` — **reverted** (it rebooted the phone at `kernel_init`).

A clean state is: fresh tree + `force-builtin-dtb.py` only.

## Files

```
dts/sm7150-motorola-common.dtsi   # SM7150 board common (trimmed from sm7150-xiaomi-common.dtsi)
dts/sm7150-motorola-hanoip.dts    # hanoip: memory size, tz override, bootargs, touch node
scripts/                          # setup/build/mkbootimg/flash + kernel-patches/
out/                              # built images (boot-hanoip-current.img is the latest clean one)
hw/                               # captured stock DTS/dmesg/partitions/iomem
PORT-NOTES.md                     # earlier working notes
```

## Device facts (verified)

- SM7150-AC, 4 GB, UFS 2.1, `userdata` on **LUN 1** (`/dev/sdb`, 4096-byte blocks).
- Panel **Ilitek ILI7807S** 1080×2460 (DSC video); splash framebuffer at **`0x9c000000`**.
- Touch **Ilitek ILI7807 TDDI** on **GENI SE6** (`spi6 @ 0xa80000`), qup10 on gpio59-62,
  reset `tlmm8`, IRQ `tlmm9`. No mainline SPI/TDDI driver yet.
- ABL: `fastboot boot` works, header v3, `fastboot flash userdata` refused by design.
