[map symbols mbr.map]

bits 16
org 0x0000


sector_size equ 512
partition_size equ 16
partition_count equ 4


; where to copy payload (0x00500 linear, just after BIOS data area)
target_segment equ 0x0050
target_offset equ 0x0000


start:

    ; copy payload to target area
    mov ax, target_segment
    mov es, ax
    mov di, target_offset
    mov ax, 0x07C0
    mov ds, ax
    mov si, payload_begin
    mov cx, payload_end - payload_begin
    cld
    rep movsb

    ; and pass control to it
    jmp target_segment:target_offset

payload_begin:

    ; payload (stage1) will be here
    times sector_size - (trailer_end - trailer_start) - ($ - start) db 0

payload_end:

trailer_start:

    ; space for partition table
    times partition_size * partition_count db 0

    ; boot signature
    db 0x55, 0xAA

trailer_end:
