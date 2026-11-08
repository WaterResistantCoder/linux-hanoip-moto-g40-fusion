#!/usr/bin/env python3
"""hanoip bring-up: simpledrm_probe paints the whole screen green then hangs.

If the screen is green -> simpledrm_probe() ran (and something later cleared it
before, i.e. fbcon is up). If blank -> simpledrm never probed.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
sd = TREE / "drivers/gpu/drm/sysfb/simpledrm.c"
s = sd.read_text()

old = """\t/* hanoip simpledrm_probe whole-screen green */
\t{
\t\tvoid __iomem *hanoip_p = ioremap(0x9c000000, 0xa22880);

\t\tif (hanoip_p) {
\t\t\tunsigned int hanoip_i;

\t\t\tfor (hanoip_i = 0; hanoip_i < 0xa22880 / 4; hanoip_i++)
\t\t\t\twritel(0xff00ff00, (u32 __iomem *)hanoip_p + hanoip_i);
\t\t}
\t}
"""
new = """\t/* hanoip simpledrm_probe whole-screen green then hang */
\t{
\t\tvoid __iomem *hanoip_p = ioremap(0x9c000000, 0xa22880);

\t\tif (hanoip_p) {
\t\t\tunsigned int hanoip_i;

\t\t\tfor (hanoip_i = 0; hanoip_i < 0xa22880 / 4; hanoip_i++)
\t\t\t\twritel(0xff00ff00, (u32 __iomem *)hanoip_p + hanoip_i);
\t\t}
\t\twhile (1)
\t\t\tcpu_relax();
\t}
"""

if "simpledrm_probe whole-screen green then hang" not in s:
    assert s.count(old) == 1, f"green block {s.count(old)}"
    sd.write_text(s.replace(old, new, 1))

print("paint-simpledrm-hang: simpledrm_probe paints green then hangs")
