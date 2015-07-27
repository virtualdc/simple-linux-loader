MEMORY
{
    ram : org = 0x00001000, len = 0x00010000
}

SECTIONS
{
    .out :
    {
        entry.o
        *(.text*)
        *(.data*)
    } > ram
}


OUTPUT_FORMAT(elf32-i386)
OUTPUT_ARCH(i386)
