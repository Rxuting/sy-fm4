/* SY FM4's MAIN OS side, linked where the boot stub copies it (0x47000000:
 * DDR above the OS's bss end 0x4554da50 and below its stack, which nothing
 * in MAIN OS 1.40A addresses). The entry table comes first. */
ENTRY(fm4m_entries)
SECTIONS
{
    . = 0x47000000;
    .text : {
        KEEP(*(.entries))
        *(.text .text.*)
        *(.rodata .rodata.*)
        . = ALIGN(4);
        *(.data .data.*)
        . = ALIGN(4);
    }
    __blob_end = .;
    .bss (NOLOAD) : {
        *(.bss .bss.* COMMON)
        . = ALIGN(4);
    }
    __bss_end = .;
    /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
