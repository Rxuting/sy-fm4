/* The SY FM4 engine blob on the Syntakt's second CPU: linked where the boot
 * stub copies it. The entry table comes first, at a fixed place. */
ENTRY(fm4_entries)
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
