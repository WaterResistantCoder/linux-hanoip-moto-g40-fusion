#!/usr/bin/env python3
"""hanoip bring-up: finer checkpoints inside setup_arch before paging_init.

  post-DTB yellow -> post-parse_early_param blue -> post-arm64_memblock_init white
  -> post-paging_init red -> pre-rest_init blue(rest) -> arch_initcall cyan
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))

def band(color, tag):
    return f"""\t/* hanoip {tag} */
\t{{
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

sc = TREE / "arch/arm64/kernel/setup.c"
s = sc.read_text()

if "post-parse_early_param blue" not in s:
    old = "\tparse_early_param();\n"
    assert s.count(old) == 1, f"parse_early_param {s.count(old)}"
    s = s.replace(old, old + "\n" + band("0xff0000ff", "post-parse_early_param blue"))
    sc.write_text(s)

s = sc.read_text()
if "post-memblock white" not in s:
    old = "\tarm64_memblock_init();\n"
    assert s.count(old) == 1, f"arm64_memblock_init {s.count(old)}"
    s = s.replace(old, old + "\n" + band("0xffffffff", "post-memblock white"))
    sc.write_text(s)

print("paint-fine: added post-parse_early_param blue and post-memblock white")
