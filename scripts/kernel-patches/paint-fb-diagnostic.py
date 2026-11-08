#!/usr/bin/env python3
"""hanoip bring-up: paint the ABL framebuffer so we can see the kernel is alive.

Two paints, independent of the device tree:
  1. very early in setup_arch() (early_ioremap) -> magenta, proves the kernel
     executes at all;
  2. an arch_initcall (full ioremap of the panel) -> green, proves it reaches
     initcalls.

If the panel never changes colour, the kernel is not running on this device.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
sc = TREE / "arch/arm64/kernel/setup.c"
s = sc.read_text()

if "hanoip_fb_paint_early" not in s:
    old = "\tearly_fixmap_init();\n\tearly_ioremap_init();\n"
    new = old + (
        "\n\t/* hanoip bring-up: paint the ABL framebuffer magenta, pre-DTB */\n"
        "\t{\n"
        "\t\tvoid __iomem *hanoip_fb_paint_early = early_ioremap(0x9c000000, PAGE_SIZE);\n"
        "\t\tif (hanoip_fb_paint_early) {\n"
        "\t\t\tunsigned int hanoip_i;\n"
        "\t\t\tfor (hanoip_i = 0; hanoip_i < PAGE_SIZE / 4; hanoip_i++)\n"
        "\t\t\t\t__raw_writel(0x00ff00ff,\n"
        "\t\t\t\t\t     (u32 __iomem *)hanoip_fb_paint_early + hanoip_i);\n"
        "\t\t}\n"
        "\t}\n"
    )
    assert s.count(old) == 1, f"early marker count {s.count(old)}"
    s = s.replace(old, new)

if "hanoip_fb_paint_late" not in s:
    s += (
        "\n/* hanoip bring-up: paint the whole panel green once ioremap is up */\n"
        "static int __init hanoip_fb_paint_late(void)\n"
        "{\n"
        "\tvoid __iomem *fb = ioremap(0x9c000000, 0xa00000);\n"
        "\tunsigned int i;\n"
        "\n"
        "\tif (!fb)\n"
        "\t\treturn 0;\n"
        "\tfor (i = 0; i < 0xa00000 / 4; i++)\n"
        "\t\twritel(0x0000ff00, (u32 __iomem *)fb + i);\n"
        "\treturn 0;\n"
        "}\n"
        "arch_initcall(hanoip_fb_paint_late);\n"
    )

sc.write_text(s)
print("paint-fb: patched setup.c (early magenta + arch_initcall green)")
