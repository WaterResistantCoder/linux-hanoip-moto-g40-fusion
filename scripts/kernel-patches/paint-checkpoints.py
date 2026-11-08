#!/usr/bin/env python3
"""hanoip bring-up: add checkpoints after setup_machine_fdt() and at initcalls.

Band 0 (top 1 MiB) is repainted by whichever checkpoint is reached last:
  head.S                -> green
  setup_arch (pre-DTB)  -> magenta   (already present)
  setup_arch (post-DTB) -> yellow    (added here)
  arch_initcall         -> cyan      (changed from whole-screen green)

So one boot shows the furthest point reached.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))

PAINT = """\t{{
\t\textern void early_iounmap(void __iomem *addr, unsigned long size);
\t\tunsigned long hanoip_off;

\t\tfor (hanoip_off = 0; hanoip_off < 0x100000; hanoip_off += PAGE_SIZE) {{
\t\t\tvoid __iomem *p = early_ioremap(0x9c000000 + hanoip_off, PAGE_SIZE);

\t\t\tif (p) {{
\t\t\t\tunsigned int hanoip_i;

\t\t\t\tfor (hanoip_i = 0; hanoip_i < PAGE_SIZE / 4; hanoip_i++)
\t\t\t\t\t__raw_writel({color}, (u32 __iomem *)p + hanoip_i);
\t\t\t\tearly_iounmap(p, PAGE_SIZE);
\t\t\t}}
\t\t}}
\t}}
"""

# 1) checkpoint right after setup_machine_fdt() -> yellow
sc = TREE / "arch/arm64/kernel/setup.c"
s = sc.read_text()
if "post-dtb yellow" not in s:
    old = "\tsetup_machine_fdt(__fdt_pointer);\n"
    new = old + "\n\t/* hanoip post-dtb yellow */\n" + PAINT.format(color="0x00ffff00")
    assert s.count(old) == 1, f"setup_machine_fdt marker {s.count(old)}"
    s = s.replace(old, new)
    sc.write_text(s)

# 2) arch_initcall checkpoint -> cyan band 2 (instead of whole-screen green)
if "hanoip_fb_paint_late" in s:
    s = sc.read_text()
    old = """\tfor (i = 0; i < 0xa00000 / 4; i++)
\t\twritel(0x0000ff00, (u32 __iomem *)fb + i);
\treturn 0;"""
    new = """\tfor (i = 0; i < 0x100000 / 4; i++)
\t\twritel(0x0000ffff, (u32 __iomem *)fb + i);
\treturn 0;"""
    if old in s:
        sc.write_text(s.replace(old, new))
        s = sc.read_text()

# 3) the arch_initcall paints at 0x9c000000 already (band 0) -> make it cyan band 0
print("paint-checkpoints: added post-DTB yellow, arch_initcall cyan")
