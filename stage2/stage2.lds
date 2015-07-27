MEMORY
{
    ram : org = 0x00001000, len = 0x00010000
}

SECTIONS
{
    .out :
    {
        *(.entry)
        *(.bioscall)
        *(.text*)
        *(.data*)
        *(.rodata*)
    } > ram
}


OUTPUT_FORMAT(elf32-i386)
OUTPUT_ARCH(i386)
