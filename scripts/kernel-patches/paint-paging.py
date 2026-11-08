#!/usr/bin/env python3
"""hanoip bring-up: checkpoints inside paging_init().

  paging_init start purple -> post-map_mem orange -> (setup_arch continues)
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))

def band(color, tag):
    return f"""\t/* hanoip {tag} */
\t{{
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

mm = TREE / "arch/arm64/mm/mmu.c"
s = mm.read_text()

if "paging_init start purple" not in s:
    old = "void __init paging_init(void)\n{\n\tmap_mem();\n"
    new = ("void __init paging_init(void)\n{\n"
           + band("0xff800080", "paging_init start purple") + "\n"
           + "\tmap_mem();\n\n"
           + band("0xffff8000", "post-map_mem orange") + "\n")
    assert s.count(old) == 1, f"paging_init marker {s.count(old)}"
    s = s.replace(old, new)
    mm.write_text(s)

print("paint-paging: added start-of-paging_init purple and post-map_mem orange")
