bits 16

start:
    mov eax, 0x01234567

    times 512 - ($ - start) -2 db 0xFF
    db 0x55, 0xAA
