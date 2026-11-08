#!/usr/bin/env python3
"""hanoip bring-up: checkpoint after simpledrm's fbdev setup."""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
sd = TREE / "drivers/gpu/drm/sysfb/simpledrm.c"
s = sd.read_text()

if "simpledrm post-client pink" not in s:
    old = "\tdrm_client_setup(dev, sdev->sysfb.fb_format);\n\n\treturn 0;\n"
    new = ("\tdrm_client_setup(dev, sdev->sysfb.fb_format);\n\n"
           "\t/* hanoip simpledrm post-client pink */\n"
           "\t{\n"
           "\t\tvoid __iomem *p = ioremap(0x9c000000, 0x100000);\n"
           "\t\tunsigned int i;\n\n"
           "\t\tif (p)\n"
           "\t\t\tfor (i = 0; i < 0x100000 / 4; i++)\n"
           "\t\t\t\twritel(0xffff0080, (u32 __iomem *)p + i);\n"
           "\t}\n\n"
           "\treturn 0;\n")
    assert s.count(old) == 1, f"drm_client_setup {s.count(old)}"
    sd.write_text(s.replace(old, new, 1))

print("paint-simpledrm: added post-client pink")
