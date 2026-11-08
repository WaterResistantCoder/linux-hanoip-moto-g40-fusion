#!/usr/bin/env python3
"""hanoip bring-up: paint the framebuffer green at the first kernel instruction.

Runs in arch/arm64/kernel/head.S at primary_entry, MMU/caches off, so it writes
physical 0x9c000000 directly -- exactly what the working control payload does.
If the panel is green, the kernel reaches head.S; if not, the kernel never runs.
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
hs = TREE / "arch/arm64/kernel/head.S"
s = hs.read_text()

if "hanoip_head_paint" not in s:
    old = "\tbl\trecord_mmu_state\n\tbl\tpreserve_boot_args\n"
    new = old + (
        "\n\t/* hanoip_head_paint: paint framebuffer green (MMU off) */\n"
        "\tmovz\tx9, #0x9c00, lsl #16\n"
        "\tmov\tw10, #0xff00ff00\n"
        "\tmovz\tx11, #0x4, lsl #16\t\t// 0x40000 words = 1 MiB\n"
        "90:\tstr\tw10, [x9], #4\n"
        "\tsubs\tx11, x11, #1\n"
        "\tb.ne\t90b\n"
    )
    assert s.count(old) == 1, f"head.S marker count {s.count(old)}"
    hs.write_text(s.replace(old, new))

print("paint-head: patched arch/arm64/kernel/head.S")
