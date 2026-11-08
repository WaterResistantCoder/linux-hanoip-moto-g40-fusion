#!/usr/bin/env python3
"""hanoip bring-up: checkpoints at end of setup_arch and just before rest_init.

  ... post-DTB yellow -> post-paging_init red -> pre-rest_init blue -> arch_initcall cyan

Uses ioremap() (Device/non-cacheable) because the linear map is cacheable and the
display engine would not see those writes.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))

RED = """\t/* hanoip post-paging_init red */
\t{
\t\tvoid __iomem *hanoip_p = ioremap(0x9c000000, 0x100000);

\t\tif (hanoip_p) {
\t\t\tunsigned int hanoip_i;

\t\t\tfor (hanoip_i = 0; hanoip_i < 0x100000 / 4; hanoip_i++)
\t\t\t\twritel(0xffff0000, (u32 __iomem *)hanoip_p + hanoip_i);
\t\t}
\t}
"""

BLUE = """\t/* hanoip pre-rest_init blue */
\t{
\t\tvoid __iomem *hanoip_p = ioremap(0x9c000000, 0x100000);

\t\tif (hanoip_p) {
\t\t\tunsigned int hanoip_i;

\t\t\tfor (hanoip_i = 0; hanoip_i < 0x100000 / 4; hanoip_i++)
\t\t\t\twritel(0xff0000ff, (u32 __iomem *)hanoip_p + hanoip_i);
\t\t}
\t}
"""

sc = TREE / "arch/arm64/kernel/setup.c"
s = sc.read_text()
if "post-paging_init red" not in s:
    old = "\tpaging_init();\n"
    assert s.count(old) == 1, f"paging_init marker {s.count(old)}"
    sc.write_text(s.replace(old, old + "\n" + RED))

mc = TREE / "init/main.c"
m = mc.read_text()
if "#include <linux/io.h>" not in m:
    m = m.replace("#include <linux/ioport.h>\n",
                  "#include <linux/ioport.h>\n#include <linux/io.h>\n", 1)
if "pre-rest_init blue" not in m:
    old = "\trest_init();\n"
    assert m.count(old) == 1, f"rest_init marker {m.count(old)}"
    m = m.replace(old, "\n" + BLUE + old)
mc.write_text(m)

print("paint-late: added post-paging_init red and pre-rest_init blue")
