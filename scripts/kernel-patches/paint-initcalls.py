#!/usr/bin/env python3
"""hanoip bring-up: paint the top band after each initcall level.

Palette by level index: 0 red, 1 green, 2 blue, 3 yellow, 4 magenta, 5 cyan,
6 white, 7 grey. The colour you see last is the last initcall level that
COMPLETED, so a hang during a level shows the previous level's colour.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
mc = TREE / "init/main.c"
s = mc.read_text()

HELPER = """
static const u32 hanoip_ic_pal[8] __initconst = {
	0xffff0000, 0xff00ff00, 0xff0000ff, 0xffffff00,
	0xffff00ff, 0xff00ffff, 0xffffffff, 0xff808080,
};

static void __init hanoip_paint_band(u32 color)
{
	void __iomem *p = ioremap(0x9c000000, 0x100000);
	unsigned int i;

	if (!p)
		return;
	for (i = 0; i < 0x100000 / 4; i++)
		writel(color, (u32 __iomem *)p + i);
	iounmap(p);
}

static void __init do_initcalls(void)
"""

if "hanoip_ic_pal" not in s:
    assert s.count("static void __init do_initcalls(void)\n") == 1
    s = s.replace("static void __init do_initcalls(void)\n", HELPER, 1)
    old = ("\t\tdo_initcall_level(level, command_line);\n\t}\n")
    new = ("\t\tdo_initcall_level(level, command_line);\n"
           "\t\thanoip_paint_band(hanoip_ic_pal[level % 8]);\n"
           "\t}\n")
    assert s.count(old) == 1, f"do_initcall_level marker {s.count(old)}"
    s = s.replace(old, new, 1)
    mc.write_text(s)

print("paint-initcalls: added per-level top-band paints")
