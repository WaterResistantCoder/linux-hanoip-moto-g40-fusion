#!/usr/bin/env python3
"""hanoip bring-up: three independent full-width bands (whole-screen thirds).

  top third    yellow  -> of_platform created the /chosen simple-framebuffer dev
  middle third green   -> simpledrm_probe() ran
  bottom third blue    -> all initcalls completed (kernel_init reached)

All three can be visible at once, so one boot shows how far it got.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
THIRD = 0xa22880 // 3

def band(idx, color, tag):
    return (f"\t/* hanoip {tag} */\n"
            "\t{\n"
            f"\t\tvoid __iomem *hanoip_p = ioremap(0x9c000000 + {idx} * 0x{THIRD:x}, 0x{THIRD:x});\n"
            "\t\tunsigned int hanoip_i;\n\n"
            "\t\tif (hanoip_p)\n"
            f"\t\t\tfor (hanoip_i = 0; hanoip_i < 0x{THIRD:x} / 4; hanoip_i++)\n"
            f"\t\t\t\twritel({color}, (u32 __iomem *)hanoip_p + hanoip_i);\n"
            "\t}\n")

def ensure_io(path):
    s = path.read_text()
    if "#include <linux/io.h>" not in s:
        s = s.replace("#include <linux/module.h>\n",
                      "#include <linux/module.h>\n#include <linux/io.h>\n", 1)
        path.write_text(s)

# 1) of_platform: after creating the /chosen simple-framebuffer device
p = TREE / "drivers/of/platform.c"
s = p.read_text()
if "band-top yellow" not in s:
    ensure_io(p); s = p.read_text()
    old = "\t\t\tof_platform_device_create(node, NULL, NULL);\n\t\t\tof_node_put(node);\n"
    assert s.count(old) == 1, f"of_platform dev create {s.count(old)}"
    s = s.replace(old, old + "\n" + band(0, "0xffffff00", "band-top yellow"), 1)
    p.write_text(s)

# 2) simpledrm probe entry
p = TREE / "drivers/gpu/drm/sysfb/simpledrm.c"
s = p.read_text()
if "band-mid green" not in s:
    ensure_io(p); s = p.read_text()
    old = ("static int simpledrm_probe(struct platform_device *pdev)\n{\n"
           "\tstruct simpledrm_device *sdev;\n")
    assert s.count(old) == 1, f"simpledrm_probe {s.count(old)}"
    s = s.replace(old, old + band(1, "0xff00ff00", "band-mid green"), 1)
    p.write_text(s)

# 3) kernel_init: after all initcalls, before running init
p = TREE / "init/main.c"
s = p.read_text()
if "band-bottom blue" not in s:
    ensure_io(p); s = p.read_text()
    old = "\tdo_sysctl_args();\n"
    assert s.count(old) == 1, f"do_sysctl_args {s.count(old)}"
    s = s.replace(old, old + "\n" + band(2, "0xff0000ff", "band-bottom blue"), 1)
    p.write_text(s)

print("diagnose: added top(yellow)/mid(green)/bottom(blue) bands")
