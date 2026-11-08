/*
 * hanoip bring-up control payload WITH an arm64 Linux Image header.
 *
 * Qualcomm ABL only treats a blob as a kernel if it carries the arm64 Image
 * header (magic "ARM\x64"), like the ios-sweet shim does. Fill the whole
 * 1080x2460 framebuffer at 0x9c000000 green, then busy-loop.
 *
 * If the panel goes green: ABL boots our image format and 0x9c000000 is
 * writable -> any later failure is inside the Linux kernel.
 */
	.section .text
	.global _start
_start:
	b	entry			/* code0: branch to kernel start */
	.long	0			/* code1 / reserved */
	.quad	0			/* text_offset */
	.quad	_end - _start		/* image_size */
	.quad	0xa			/* flags: LE, 4K pages, place anywhere in 4G */
	.quad	0			/* res2 */
	.quad	0			/* res3 */
	.quad	0			/* res4 */
	.ascii	"ARM\x64"		/* magic at offset 56 */
	.long	0			/* res5 */
entry:
	movz	x0, #0x9c00, lsl #16		/* 0x9c000000 */
	mov	w1, #0xff00ff00			/* ARGB green */
	movz	x2, #0xa2, lsl #16		/* ~1080*2460*4 bytes */
1:
	str	w1, [x0], #4
	subs	x2, x2, #1
	b.ne	1b
2:
	b	2b
_end:
