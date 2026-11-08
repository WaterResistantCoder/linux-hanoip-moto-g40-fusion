#!/usr/bin/env python3
"""hanoip bring-up: make the setup_arch() checkpoint a full 1 MiB magenta band.

The head.S paint (green, 1 MiB) proves the kernel's first instruction runs.
This checkpoint proves whether control reaches setup_arch() (after the MMU and
early_ioremap are up): it repaints the same top band magenta. early_ioremap can
only map a page at a time, so map/paint/unmap a page at a time.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
sc = TREE / "arch/arm64/kernel/setup.c"
s = sc.read_text()

old = """\t/* hanoip bring-up: paint the ABL framebuffer magenta, pre-DTB */
\t{
\t\tvoid __iomem *hanoip_fb_paint_early = early_ioremap(0x9c000000, PAGE_SIZE);
\t\tif (hanoip_fb_paint_early) {
\t\t\tunsigned int hanoip_i;
\t\t\tfor (hanoip_i = 0; hanoip_i < PAGE_SIZE / 4; hanoip_i++)
\t\t\t\t__raw_writel(0x00ff00ff,
\t\t\t\t\t     (u32 __iomem *)hanoip_fb_paint_early + hanoip_i);
\t\t}
\t}
"""

new = """\t/* hanoip bring-up: repaint the top 1 MiB magenta (proves setup_arch) */
\t{
\t\textern void early_iounmap(void __iomem *addr, unsigned long size);
\t\tunsigned long hanoip_off;

\t\tfor (hanoip_off = 0; hanoip_off < 0x100000; hanoip_off += PAGE_SIZE) {
\t\t\tvoid __iomem *p = early_ioremap(0x9c000000 + hanoip_off, PAGE_SIZE);

\t\t\tif (p) {
\t\t\t\tunsigned int hanoip_i;

\t\t\t\tfor (hanoip_i = 0; hanoip_i < PAGE_SIZE / 4; hanoip_i++)
\t\t\t\t\t__raw_writel(0x00ff00ff, (u32 __iomem *)p + hanoip_i);
\t\t\t\tearly_iounmap(p, PAGE_SIZE);
\t\t\t}
\t\t}
\t}
"""

if "repaint the top 1 MiB magenta" not in s:
    assert s.count(old) == 1, f"setup.c paint block count {s.count(old)}"
    sc.write_text(s.replace(old, new))

print("paint-setup-big: setup_arch() now repaints 1 MiB magenta")
