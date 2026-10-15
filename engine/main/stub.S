/* MAIN OS boot stub for SY FM4. Appended to section 3 right after the image
 * (0x40330b90), followed by the blob. The entry (0x400004e8) calls
 * `jsr 0x4000045c` (SRAM initial data) and `jsr 0x400004b2` (clear bss from
 * 0x40322000, which covers this tail) at 0x4000053e; the patcher makes that
 * `jsr stub.l; nop`. The stub copies the blob to its link address and clears
 * its bss, runs the blob's boot hook (fm4m_boot), then makes both calls, the second as a tail call, so it returns
 * to 0x40000544 before anything is cleared under it. */
    .text
    .globl stub
stub:
    lea     -16(%sp),%sp
    movem.l %d0-%d1/%a0-%a1,(%sp)
    movea.l #BLOB_ADDR,%a1
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
3:  jsr     BOOT_FN
    movem.l (%sp),%d0-%d1/%a0-%a1
    lea     16(%sp),%sp
    jsr     0x4000045c
    jmp     0x400004b2
