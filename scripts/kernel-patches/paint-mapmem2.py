#!/usr/bin/env python3
"""hanoip bring-up: split the two kernel __map_memblock() calls in map_mem().

  post-kfence teal -> post-kernel-text maroon -> pre-loop navy
"""
import os
import pathlib

TREE = pathlib.Path(os.environ.get("TREE", "/kernel"))
mm = TREE / "arch/arm64/mm/mmu.c"
s = mm.read_text()

if "post-kernel-text maroon" not in s:
    old = ("\t__map_memblock(kernel_start, init_begin, pgprot_tagged(PAGE_KERNEL),\n"
           "\t\t       flags);\n")
    assert s.count(old) == 1, f"kernel-text marker {s.count(old)}"
    s = s.replace(old, old + "\n\thanoip_paint(0xff800000);\t/* hanoip post-kernel-text maroon */\n", 1)
    mm.write_text(s)

print("paint-mapmem2: added post-kernel-text maroon")
