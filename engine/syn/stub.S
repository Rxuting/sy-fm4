/* Section 7 boot stub for SY FM4. It lives at 0x4004f5c0, 256 bytes of the
 * image's zero area that nothing in section 7 reads or writes (measured over
 * a boot and a render in digiemu), below the bss section 7 clears.
 * Called from 0x400010b4, the entry's `jsr 0x400004bc; jsr 0x40000512` (copy
 * the SRAM's initial data, then clear bss from 0x4004f6e0), before the bss
 * clear: the blob is appended after the image (0x4005df10), inside that bss.
 * Unless the blob is already at its link address (its entry table there),
 * copies it there and clears its own bss; then makes both original calls,
 * the second as a tail call, so it returns to 0x400010bc. */
    .text
    .globl stub
stub:
    lea     -16(%sp),%sp
    movem.l %d0-%d1/%a0-%a1,(%sp)
    movea.l #BLOB_ADDR,%a1
    move.l  (%a1),%d0
    cmpi.l  #BLOB_ENTRY0,%d0
    beq.s   3f
    movea.l #BLOB_SRC,%a0
    move.l  #BLOB_WORDS,%d0
1:  move.l  (%a0)+,(%a1)+
    subq.l  #1,%d0
    bne.s   1b
    move.l  #BSS_WORDS,%d0
    beq.s   3f
2:  clr.l   (%a1)+
    subq.l  #1,%d0
    bne.s   2b
3:  movem.l (%sp),%d0-%d1/%a0-%a1
    lea     16(%sp),%sp
    jsr     0x400004bc
    jmp     0x40000512
