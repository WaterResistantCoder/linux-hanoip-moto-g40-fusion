#!/usr/bin/env python3
"""hanoip bring-up: if simpledrm probes at all, paint the WHOLE screen green.

Decisive: a full green screen means simpledrm_probe() ran. If it stays the ABL
logo, simpledrm never probed (device not created, or probe failed).
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
sd = TREE / "drivers/gpu/drm/sysfb/simpledrm.c"
s = sd.read_text()

old = """\t/* hanoip simpledrm_probe violet */
\t{
\t\tvoid __iomem *hanoip_p = ioremap(0x9c000000, 0x100000);

\t\tif (hanoip_p) {
\t\t\tunsigned int hanoip_i;

\t\t\tfor (hanoip_i = 0; hanoip_i < 0x100000 / 4; hanoip_i++)
\t\t\t\twritel(0xff8000ff, (u32 __iomem *)hanoip_p + hanoip_i);
\t\t}
\t}
"""
new = """\t/* hanoip simpledrm_probe whole-screen green */
\t{
\t\tvoid __iomem *hanoip_p = ioremap(0x9c000000, 0xa22880);

\t\tif (hanoip_p) {
\t\t\tunsigned int hanoip_i;

\t\t\tfor (hanoip_i = 0; hanoip_i < 0xa22880 / 4; hanoip_i++)
\t\t\t\twritel(0xff00ff00, (u32 __iomem *)hanoip_p + hanoip_i);
\t\t}
\t}
"""

if "simpledrm_probe whole-screen green" not in s:
    assert s.count(old) == 1, f"violet block {s.count(old)}"
    sd.write_text(s.replace(old, new, 1))

print("paint-simpledrm-whole: simpledrm_probe now paints the whole screen green")
