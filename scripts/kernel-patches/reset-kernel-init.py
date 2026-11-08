#!/usr/bin/env python3
"""hanoip bring-up: reset the phone at the start of kernel_init().

Binary signal: if the phone reboots back to fastboot by itself, kernel_init()
was reached (start_kernel/rest_init completed), so a later hang is in the
initcalls or userspace. If it does not reboot, the hang is before kernel_init.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
mc = TREE / "init/main.c"
s = mc.read_text()

if "#include <linux/reboot.h>" not in s:
    s = s.replace("#include <linux/init.h>\n", "#include <linux/init.h>\n#include <linux/reboot.h>\n", 1)

if "hanoip reset at kernel_init" not in s:
    old = "\twait_for_completion(&kthreadd_done);\n"
    assert s.count(old) == 1, f"kthreadd_done {s.count(old)}"
    new = ("\t/* hanoip reset at kernel_init */\n"
           "\temergency_restart();\n\n"
           "\twait_for_completion(&kthreadd_done);\n")
    s = s.replace(old, new, 1)
    mc.write_text(s)

print("reset-kernel-init: kernel_init() now resets the phone")
