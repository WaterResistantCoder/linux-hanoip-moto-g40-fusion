#!/usr/bin/env python3
"""hanoip bring-up: checkpoints inside map_mem().

  paging_init start purple (existing)
  -> post arm64_kfence_map_pool teal
  -> pre loop (kernel maps done) navy
  -> per memblock region: palette[index % 8]
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
mm = TREE / "arch/arm64/mm/mmu.c"
s = mm.read_text()

HELPER = """
static const u32 hanoip_pal[8] __initconst = {
	0xffff0000, 0xff00ff00, 0xff0000ff, 0xffffff00,
	0xffff00ff, 0xff00ffff, 0xffffffff, 0xff808080,
};

static void __init hanoip_paint(u32 color)
{
	unsigned long off;

	for (off = 0; off < 0x100000; off += PAGE_SIZE) {
		void __iomem *p = early_ioremap(0x9c000000 + off, PAGE_SIZE);

		if (p) {
			unsigned int k;

			for (k = 0; k < PAGE_SIZE / 4; k++)
				__raw_writel(color, (u32 __iomem *)p + k);
			early_iounmap(p, PAGE_SIZE);
		}
	}
}

static void __init map_mem(void)
"""

if "hanoip_paint" not in s:
    s = s.replace("static void __init map_mem(void)\n", HELPER, 1)
    # after arm64_kfence_map_pool()
    old = "\tarm64_kfence_map_pool();\n"
    s = s.replace(old, old + "\n\thanoip_paint(0xff008080);\t/* hanoip post-kfence teal */\n", 1)
    # before the memory-bank loop
    old2 = "\t/* map all the memory banks */\n\tfor_each_mem_range(i, &start, &end) {\n"
    new2 = ("\t/* map all the memory banks */\n"
            "\thanoip_paint(0xff000080);\t/* hanoip pre-loop navy */\n"
            "\tfor_each_mem_range(i, &start, &end) {\n"
            "\t\tstatic unsigned int hanoip_n;\n")
    assert s.count(old2) == 1, f"loop marker {s.count(old2)}"
    s = s.replace(old2, new2, 1)
    # after __map_memblock in the loop
    old3 = "\t\t__map_memblock(start, end, pgprot_tagged(PAGE_KERNEL),\n\t\t\t       flags);\n\t}\n"
    new3 = ("\t\t__map_memblock(start, end, pgprot_tagged(PAGE_KERNEL),\n"
            "\t\t\t       flags);\n"
            "\t\thanoip_paint(hanoip_pal[hanoip_n++ % 8]);\n"
            "\t}\n")
    assert s.count(old3) == 1, f"map_memblock loop marker {s.count(old3)}"
    s = s.replace(old3, new3, 1)
    mm.write_text(s)

print("paint-mapmem: instrumented map_mem()")
