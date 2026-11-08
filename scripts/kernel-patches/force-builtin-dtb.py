#!/usr/bin/env python3
"""Force the hanoip mainline DTB to be used, ignoring the bootloader's DTB.

Moto ABL passes the *stock downstream* hanoip DTB in x0 (it adds linux,initrd-*
to it and hands it over). Mainline arm64 does no machine matching, so the kernel
boots happily with the wrong tree and never finds the simple-framebuffer node ->
nothing is drawn on the panel and it stays on the ABL splash.

Fix: compile our DTB into the kernel and point __fdt_pointer at it, so the
bootloader's DTB is ignored. Run inside the kernel tree (cwd = /kernel, or $TREE).

This is a bring-up hack and is intentionally kept as a separate, removable patch.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
DTB = "arch/arm64/boot/dts/qcom/sm7150-motorola-hanoip.dtb"

# 1) assembly blob with the DTB incbin'd into .init.data
asm = TREE / "arch/arm64/kernel/hanoip_dtb.S"
asm.write_text(
    "/* SPDX-License-Identifier: GPL-2.0-only */\n"
    '\t.section .rodata, "a"\n'
    "\t.balign 8\n"
    "\t.global hanoip_dtb_start\n"
    "\t.global hanoip_dtb_end\n"
    "hanoip_dtb_start:\n"
    f'\t.incbin "{DTB}"\n'
    "hanoip_dtb_end:\n"
    "\t.balign 8\n"
)

# 2) build the blob, after the DTB exists
mk = TREE / "arch/arm64/kernel/Makefile"
s = mk.read_text()
if "hanoip_dtb" not in s:
    s += (
        "\n# hanoip: force the mainline DTB (ABL passes the stock downstream one)\n"
        "obj-y += hanoip_dtb.o\n"
        f"$(obj)/hanoip_dtb.o: $(srctree)/{DTB}\n"
    )
    mk.write_text(s)

# 3) override __fdt_pointer in setup_arch()
sc = TREE / "arch/arm64/kernel/setup.c"
s = sc.read_text()
if "hanoip_dtb_start" not in s:
    old = "\tsetup_machine_fdt(__fdt_pointer);"
    new = (
        "\t/*\n"
        "\t * hanoip: ABL passes the stock downstream DTB in x0 and mainline\n"
        "\t * arm64 does no machine matching, so it boots with the wrong tree.\n"
        "\t * Point __fdt_pointer at the mainline DTB built into the image.\n"
        "\t */\n"
        "\t{\n"
        "\t\textern char hanoip_dtb_start[];\n"
        "\t\t__fdt_pointer = __pa_symbol(hanoip_dtb_start);\n"
        "\t}\n"
        "\tsetup_machine_fdt(__fdt_pointer);"
    )
    assert s.count(old) == 1, f"setup.c marker count = {s.count(old)}"
    sc.write_text(s.replace(old, new))

print("force-builtin-dtb: patched hanoip_dtb.S, arch/arm64/kernel/Makefile, setup.c")
