#!/usr/bin/env python3
"""hanoip bring-up: paint the WHOLE screen after each initcall level.

The colour you see last is the last level that COMPLETED. Palette by level:
  0 early=red 1 pure=green 2 core=blue 3 postcore=yellow 4 arch=magenta
  5 subsys=cyan 6 fs=white 7 device=grey 8 late=red
So a hang during a level shows the previous level's colour.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
mc = TREE / "init/main.c"
s = mc.read_text()

if "#include <linux/io.h>" not in s:
    s = s.replace("#include <linux/ioport.h>\n",
                  "#include <linux/ioport.h>\n#include <linux/io.h>\n", 1)

HELPER = """
static const u32 hanoip_lvl_pal[8] __initconst = {
	0xffff0000, 0xff00ff00, 0xff0000ff, 0xffffff00,
	0xffff00ff, 0xff00ffff, 0xffffffff, 0xff808080,
};

static void __init hanoip_paint_all(u32 color)
{
	void __iomem *p = ioremap(0x9c000000, 0xa22880);
	unsigned int i;

	if (!p)
		return;
	for (i = 0; i < 0xa22880 / 4; i++)
		writel(color, (u32 __iomem *)p + i);
}

static void __init do_initcalls(void)
"""

if "hanoip_lvl_pal" not in s:
    assert s.count("static void __init do_initcalls(void)\n") == 1
    s = s.replace("static void __init do_initcalls(void)\n", HELPER, 1)
    old = "\t\tdo_initcall_level(level, command_line);\n\t}\n"
    new = ("\t\tdo_initcall_level(level, command_line);\n"
           "\t\thanoip_paint_all(hanoip_lvl_pal[level % 8]);\n"
           "\t}\n")
    assert s.count(old) == 1, f"do_initcall_level marker {s.count(old)}"
    s = s.replace(old, new, 1)
    mc.write_text(s)

print("paint-levels: whole-screen paint after each initcall level")
