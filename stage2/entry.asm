bits 16

extern main

section .entry


stage2_entry:

    ; stage2 entry point
    ; we have drive number in DL

    ; setup DS
    xor ax, ax
    mov ds, ax

    ; disable interrupts
    cli

    ; load GDT
    lgdt [gdt_ptr]

    ; enable protected mode
    mov eax, cr0
    or al, 1
    mov cr0, eax

    ; far jump to reload CS
    jmp 0x10 : stage2_pm

stage2_pm:

    ; we are in flat protected mode now
bits 32

    ; setup segment regs and stack
    mov ax, 0x18
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    movzx ebx, sp
    mov ss, ax
    mov esp, ebx

    ; pass drive number to main
    movzx edx, dl
    push edx
    call main

    ; WTF?! main() should not return control!
    jmp $+0

; GDT_ENTRY <base>, <limit>, <access>, <flags>
;   base - linear address where segment starts
;   limit - size of segment in bytes (Gr=0) or 4k pages (Gr=1)
;   access - bit or of GDT_ACCESS_*
;   flags - bit or of GDT_FLAG_*
%macro GDT_ENTRY 4
    db %2 & 0xFF
    db (%2 >> 8) & 0xFF
    db %1 & 0xFF
    db (%1 >> 8) & 0xFF
    db (%1 >> 16) & 0xFF
    db %3
    db ((%4 << 4) & 0xF0) | ((%2 >> 16) & 0xF)
    db (%1 >> 24) & 0xFF
%endmacro

GDT_ACCESS_PRESENT equ 0x80
GDT_ACCESS_RING0 equ 0x00
GDT_ACCESS_RING1 equ 0x20
GDT_ACCESS_RING2 equ 0x40
GDT_ACCESS_RING3 equ 0x60
GDT_ACCESS_ONE equ 0x10
GDT_ACCESS_EXEC equ 0x08
GDT_ACCESS_DC equ 0x04
GDT_ACCESS_RW equ 0x02
GDT_ACCESS_ACCESSED equ 0x01

GDT_FLAG_GR equ 0x08
GDT_FLAG_SZ equ 0x04


section .data

    ; GDT table for 32-bit flat mode

    align 16
gdt_begin:
    ; 0x00 - null
    GDT_ENTRY 0, 0, 0, 0
    ; 0x08 - null
    GDT_ENTRY 0, 0, 0, 0
    ; 0x10 - code
    GDT_ENTRY 0x00000000, 0xFFFFF, GDT_ACCESS_PRESENT | GDT_ACCESS_RING0 | \
        GDT_ACCESS_ONE | GDT_ACCESS_EXEC | GDT_ACCESS_RW, (GDT_FLAG_SZ | GDT_FLAG_GR)
    ; 0x18 - data
    GDT_ENTRY 0x00000000, 0xFFFFF, GDT_ACCESS_PRESENT | GDT_ACCESS_RING0 | \
        GDT_ACCESS_ONE | GDT_ACCESS_RW, (GDT_FLAG_SZ | GDT_FLAG_GR)
    ; 0x20 - real mode code segment
    GDT_ENTRY 0x00000000, 0xFFFFF, GDT_ACCESS_PRESENT | GDT_ACCESS_RING0 | \
        GDT_ACCESS_ONE | GDT_ACCESS_EXEC | GDT_ACCESS_RW, 0
    ; 0x24 - real mode data segment
    GDT_ENTRY 0x00000000, 0xFFFFF, GDT_ACCESS_PRESENT | GDT_ACCESS_RING0 | \
        GDT_ACCESS_ONE | GDT_ACCESS_RW, 0
gdt_end:

gdt_ptr:
    dw gdt_end - gdt_begin
    dd gdt_begin
