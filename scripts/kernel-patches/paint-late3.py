#!/usr/bin/env python3
"""hanoip bring-up: checkpoints after the initcalls.

  arch_initcall cyan -> kernel_init (before init) azure -> simpledrm_probe violet
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))

def paint(color, tag):
    return f"""\t/* hanoip {tag} */
\t{{
\t\tvoid __iomem *hanoip_p = ioremap(0x9c000000, 0x100000);

\t\tif (hanoip_p) {{
\t\t\tunsigned int hanoip_i;

\t\t\tfor (hanoip_i = 0; hanoip_i < 0x100000 / 4; hanoip_i++)
\t\t\t\twritel({color}, (u32 __iomem *)hanoip_p + hanoip_i);
\t\t}}
\t}}
"""

# 1) kernel_init, before running init
mc = TREE / "init/main.c"
m = mc.read_text()
if "kernel_init azure" not in m:
    old = "\tdo_sysctl_args();\n"
    assert m.count(old) == 1, f"do_sysctl_args {m.count(old)}"
    m = m.replace(old, old + "\n" + paint("0xff0080ff", "kernel_init azure"), 1)
    mc.write_text(m)

# 2) simpledrm_probe, at entry
sd = TREE / "drivers/gpu/drm/sysfb/simpledrm.c"
s = sd.read_text()
if "#include <linux/io.h>" not in s:
    s = s.replace("#include <linux/module.h>\n", "#include <linux/module.h>\n#include <linux/io.h>\n", 1)
if "simpledrm_probe violet" not in s:
    old = ("static int simpledrm_probe(struct platform_device *pdev)\n{\n"
           "\tstruct simpledrm_device *sdev;\n")
    new = ("static int simpledrm_probe(struct platform_device *pdev)\n{\n"
           "\tstruct simpledrm_device *sdev;\n"
           + paint("0xff8000ff", "simpledrm_probe violet"))
    assert s.count(old) == 1, f"simpledrm_probe {s.count(old)}"
    s = s.replace(old, new, 1)
    sd.write_text(s)

print("paint-late3: added kernel_init azure and simpledrm_probe violet")
