#!/usr/bin/env python3
"""hanoip bring-up: whole-screen checkpoints after the initcalls.

  do_basic_setup done   -> yellow
  console_on_rootfs done-> cyan
  kernel_init pre-init  -> blue
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
static void __init hanoip_paint_all2(u32 color)
{
	void __iomem *p = ioremap(0x9c000000, 0xa22880);
	unsigned int i;

	if (!p)
		return;
	for (i = 0; i < 0xa22880 / 4; i++)
		writel(color, (u32 __iomem *)p + i);
}

static noinline void __init kernel_init_freeable(void);
"""

def paint(color, tag):
    return f"\t/* hanoip {tag} */\n\thanoip_paint_all2({color});\n"

if "hanoip_paint_all2" not in s:
    assert s.count("static noinline void __init kernel_init_freeable(void);\n") == 1
    s = s.replace("static noinline void __init kernel_init_freeable(void);\n", HELPER, 1)

    old1 = "\tdo_basic_setup();\n"
    assert s.count(old1) == 1, f"do_basic_setup {s.count(old1)}"
    s = s.replace(old1, old1 + "\n" + paint("0xffffff00", "post do_basic_setup yellow"), 1)

    old2 = "\tconsole_on_rootfs();\n"
    assert s.count(old2) == 1, f"console_on_rootfs {s.count(old2)}"
    s = s.replace(old2, old2 + "\n" + paint("0xff00ffff", "post console_on_rootfs cyan"), 1)

    old3 = "\tif (ramdisk_execute_command) {\n"
    assert s.count(old3) == 1, f"ramdisk_execute_command {s.count(old3)}"
    s = s.replace(old3, paint("0xff0000ff", "kernel_init pre-init blue") + "\n" + old3, 1)

    mc.write_text(s)

print("paint-init: added yellow/cyan/blue whole-screen checkpoints")
