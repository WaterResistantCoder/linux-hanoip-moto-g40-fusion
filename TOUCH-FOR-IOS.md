# Fixing the ILITEK touch on iOS — findings from the mainline port

This is the distilled, actionable result of getting the **Ilitek ILI7807 TDDI** touch fully working
under mainline Linux on hanoip (Moto G40 Fusion / G60, SM7150-AC). The iOS port hit the *same* wall
(`TOUCH-FINDING.md`: "the IC's own AP/report bring-up") — the root cause turned out to be the
**firmware**, plus a few protocol details. Everything below is verified working on the real device.

## TL;DR — the three things that matter

1. **The firmware is wrong.** The chip will not run the generic `FW_TDDI_TRUNK_FB` image. It needs the
   stock Moto firmware **`FW_ILITEK_TDDI_TM.bin`** (Intel HEX text, 358761 bytes). With the wrong FW
   the chip answers AP-mode reads with the opcode echoed (`0x83 00 00 …`) and never the `0xA3` ACK —
   exactly the symptom in `TOUCH-FINDING.md`. ICE-mode register reads still work, which is why the
   chip looks alive but the AP read never does.
2. **The AP-mode SPI framing has a 2-byte offset.** Read = send `0x83`, clock `n_rx + 2` bytes,
   **ACK (`0xA3`) is at `rx[1]`, payload starts at `rx[3]`**. Write = `0x82, len_hi, len_lo, data`.
   A bare `0x83` with the payload read from `rx[0]` cannot work.
3. **Sensing must be enabled after the FW download** (`sense` func ctrl), or the FW reports valid
   `0x5a` demo packets with all-`0xff` fingers forever.

---

## 1. The firmware (the actual root cause)

- **File:** `FW_ILITEK_TDDI_TM.bin` — Intel HEX (text), size **358761**.
- **Where it lives on the phone:** `/firmware/FW_ILITEK_TDDI_TM.bin` in the **`vendor`** partition
  (Android dynamic partition `vendor_a`, inside `super`). Extract with `debugfs`:
  `debugfs -R "dump /firmware/FW_ILITEK_TDDI_TM.bin /tmp/fw.bin" vendor_a.img`
- A copy is kept in this repo at **`out/FW_ILITEK_TDDI_TM.hex`**.
- The generic `FW_TDDI_TRUNK_FB.ili` (the vendor driver's built-in blob) is **not** the right image:
  its block map is `start 0x0 end 0x1C000, 5 blocks` and its AP CRC is `8fed664b`. The stock/TM image
  is `start 0x0 end 0x1F200, 4 blocks`, AP CRC **`fea9bcbd`**, DATA `ca3e7527`, TUNING `94d9c4dd`.

If the FW download is verified by CRC, these are the values to expect from the *correct* image:

```
AP     CRC fea9bcbd   (hex == dma == iram)
DATA   CRC ca3e7527
TUNING CRC 94d9c4dd
```

## 2. SPI protocol (AP mode vs ICE mode)

The IC has two SPI personalities: the **ICE-mode hardware slave** (used for register access and the
FW download) and the **AP-mode FW slave** (used once the FW runs). They are framed differently.

### AP mode (the FW is running)

| op | bytes on the wire |
| --- | --- |
| write | `0x82`, `len_hi`, `len_lo`, `data…` |
| read  | `0x83`, then clock `n_rx + 2` bytes |

For a read the response frame is `[0] = junk, [1] = ACK (0xA3), [2] = junk, [3..] = payload`.
So: **check `rx[1] == 0xA3`**, and copy the payload from `rx[3]`.

This is `ilitek_v3_spi.c: ili_spi_write_then_read_direct()` (the stock driver):

```c
	if (!atomic_read(&ilits->ice_stat))
		offset = 2;                       /* AP mode */
	duplex_len = n_tx + n_rx + offset;
	...
	if (ilits->spi_rx[1] != SPI_ACK && !atomic_read(&ilits->ice_stat)) {
		status = DO_SPI_RECOVER;          /* no ACK -> SPI recovery */
		break;
	}
	memcpy(rxbuf, ilits->spi_rx + offset + 1, n_rx);   /* payload at rx[3] */
```

and the wrapper that adds the write length header:

```c
	if (ice) { wdata[0] = SPI_WRITE; index = 1; }      /* ICE: no length header */
	else     { wdata[0] = SPI_WRITE; wdata[1] = wlen >> 8; wdata[2] = wlen & 0xff; index = 3; }
```

Constants: `SPI_WRITE = 0x82`, `SPI_READ = 0x83`, `SPI_ACK = 0xA3`.

### ICE mode (register access / FW download)

- enter: `0x82 0x25 0x62 0x10 0x18` (stop MCU) or `0x82 0x1F 0x62 0x10 0x18` (MCU on)
- exit : `0x82 0x1B 0x62 0x10 0x18`
- write register: `0x82 0x25 addrL addrM addrH data…`
- read register : write `0x82 0x25 addrL addrM addrH`, then read `0x83` + N bytes; the value is
  `rx[0..3]` little-endian.

In ICE mode the read offset is **0**, not 2 (payload at `rx[1]` after the `0x83`).

## 3. Bring-up sequence (what actually works)

1. HW reset the chip (GPIO reset pulse), then enter ICE mode.
2. Read the chip id (ICE): expect `PID = 0x78071c03` → `Chip ID = 0x7807`.
3. **Host-download the firmware to IRAM** from `FW_ILITEK_TDDI_TM.bin`, in 2048-byte chunks, as
   ICE-mode register writes: `0x82 0x25 addrL addrM addrH data…` (address = the IRAM address).
4. Verify each block's CRC (see §4).
5. **Code reset** — ICE write `0x40040 = 0xAE` (1 byte), then exit ICE mode. This starts the MCU.
6. **Enable sensing** — send the `sense` function control (see §5). *Without this the FW never senses.*
7. Wait a moment, then AP-mode reads work: protocol version `5.6.0`, core version, panel info
   `1080x2460`, and the `0x5a` demo report packets.

Do **not** read the FW version / protocol version before step 5–6 — it will fail and may make the
driver try a host-download "recovery" loop.

## 4. The DMA CRC check — poll the right bit

If you verify the download with the chip's internal DMA CRC engine (optional but it is what proves the
image is good), the vendor code polls the **wrong bit**. The stock (`calc_hw_dma_crc`) uses:

```
0x40040 = 0x00800000, then 0x40040 = 0x00000000   ; DMA reset
0x072104 = start_addr
0x072108 = 0x80000001
0x072114 = 0x0002725C        ; NOT 0x00030000
0x072118 = 0x80000000
0x07211C = block_size
0x041016 = 0x00 ; 0x041017 = 0x03 ; 0x041016 = 0x01
0x072100 = 0x02000000        ; DMA stop  (NOT 0)
0x048006 = 0x02              ; clr int   (NOT 0x01)
0x072100 = 0x01000000        ; DMA start
poll 0x048006 for BIT1 (busy & 0x02), NOT BIT0
read CRC from 0x04101C
```

Polling bit0 instead of bit1 makes a *correct* download look corrupt (bit0 is never set; the register
reads `0x02`, i.e. bit1 = done). That wasted a lot of time here.

## 5. The `sense` function control

After the code reset, send the `sense` func ctrl — otherwise the FW reports `0x5a` packets with no
fingers no matter how you touch:

```
protocol 5.6.0:  sense_ctrl = { 0x01, 0x01, 0x01 }   (last byte = 1 = start)
sent as an AP-mode write:  0x82 len_hi len_lo 0x01 0x01 0x01
```

(The stock driver leaves sensing on by default; be explicit.)

## 6. Reading reports

Once the FW runs, the INT line asserts on a report. The report is a **43-byte demo packet**:

```
[0]    0x5A                     demo packet id
[1..4] finger 0:  x = ((b1 & 0xF0) << 4) | b2 ,  y = ((b1 & 0x0F) << 8) | b3 ,  pressure = b4
[5..40] fingers 1..9, 0xFF when not present
[41]   0x07
[42]   checksum = (-sum(bytes 0..41)) & 0xFF
```

Read it as a **bare `0x83`** (no command), triggered by the INT, with the AP framing from §2.
The stock waits for the IC's INT before reading a command response (`spi_irq` path) — the FW signals
"response ready" on INT, so gate command reads on it.

`TOUCH-FINDING.md` recorded a real captured packet: `5a 55 46 e8 02 …` → x=1350 y=1512 pressure=2.
Our port reproduces this (`[x,y]` then `DOWN: id=0, x=… y=…`).

## 7. Device facts (verified)

| thing | value |
| --- | --- |
| touch IC | Ilitek ILI7807 TDDI (PID `0x78071c03`) |
| bus | GENI SE6, `spi6 @ 0xa80000`, QUP10 on gpio 59–62 |
| CS | gpio 62 (must be muxed as **gpio** if you use a GPIO CS) |
| reset | TLMM gpio 8 (idle high, reset = low pulse, then high) |
| IRQ | TLMM gpio 9, `IRQ_TYPE_EDGE_FALLING`, active low |
| SPI | mode 0, 8 bits/word, 10 MHz after "speed up" |
| FW | `FW_ILITEK_TDDI_TM.bin` from `/firmware/` in the **vendor** partition |

## 8. Reference material

- **Stock driver source (the one that works):** `~/ios-hanoip/ilitek/` — `ilitek_v3_mmi`
  (`ilitek_v3_spi.c`, `ilitek_v3_ic.c`, `ilitek_v3_hostdl.c`, `ilitek_v3_touch.c`, `ilitek_v3.h`).
  This is the driver the vendor uses on this device; it supports ILI7807.
- **Working mainline driver:** `~/Personal/hanoip-linux` → kernel tree
  `drivers/input/touchscreen/ilitek-ipio/` (a port of the vendor `ipio_touch_driver`, with the fixes
  above applied; see `HANDOFF.md`).
- **The correct firmware:** `~/Personal/hanoip-linux/out/FW_ILITEK_TDDI_TM.hex`.

## 9. Things that did NOT matter (so don't chase them)

- The bit-banged SPI clock: the iOS sweep (10..800 NOPs) changed nothing — it is not a bus-timing issue.
- MOSI held low during reads; read length 45 vs 43; disabling preemption — none of these matter.
- The TDDI display/panel reset does not wipe the touch FW (verified: a runtime re-download with the
  panel fully up still failed the same way *with the wrong FW*).
- The SPI mode is 0; the ICE-mode slave tolerates the split command/data transfers, so the *split*
  is not the problem either — the missing piece was the FW and the AP framing/offset.
