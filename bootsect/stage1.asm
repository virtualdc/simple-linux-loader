bits 16
org 0x0000


blocklist_buffer_offset equ 0x200
sector_size equ 0x200
record_size equ 8


    ; setup DS and stack
    mov ax, cs
    mov ds, ax
    lss sp, [conf_stack_ofs]

    ; save DL (drive number)
    mov [drive_num], dl

    ; prepare to read first blocklist sector
    lea si, [conf_blocklist_lba]

read_blocklist_sector:

    ; read blocklist sector
    mov ax, ds
    mov es, ax
    mov di, blocklist_buffer_offset
    mov dl, [drive_num]
    call read_sector
    jc error

    mov si, blocklist_buffer_offset

read_data_sector:

    push si


    ; read data sector
    mov ax, [conf_stage2_seg]
    mov es, ax
    add ax, sector_size / 16
    mov [conf_stage2_seg], ax
    mov di, [conf_stage2_ofs]
    mov dl, [drive_num]
    call read_sector
    jc error

    pop si

    add si, record_size

    ; check for end of blocklist
    mov ax, [si]
    and ax, [si+2]
    and ax, [si+4]
    and ax, [si+6]
    inc ax
    jz done

    cmp si, blocklist_buffer_offset + sector_size - record_size
    jz read_blocklist_sector
    jmp read_data_sector

done:

    ; pass control to stage2
    jmp far [conf_entry_ofs]

error:
    ; TODO: display error message

.die:
    jmp .die


; read sector
; input:
;   [ds:si] - LBA of sector (8 bytes)
;   [es:di] - output buffer (512 bytes)
;   dl - drive number
; output:
;   cf - set on error
;   ah - error code
read_sector:

    ; fill DAP
    mov ax, es
    mov [dap_segment], ax
    mov [dap_offset], di
    mov ax, [si]
    mov [dap_lba], ax
    mov ax, [si+2]
    mov [dap_lba+2], ax
    mov ax, [si+4]
    mov [dap_lba+4], ax
    mov ax, [si+6]
    mov [dap_lba+6], ax

    ; read sector
    mov ah, 0x42
    lea si, [dap_size]
    int 0x13

    ret


; === variables ===

    ; drive number for int 13h
    drive_num db 0

    ; DAP structure for 13h
    dap_size db 16
    dap_unused db 0
    dap_count dw 1
    dap_offset dw 0
    dap_segment dw 0
    dap_lba dq 0



; ======= configuration block =====
; MUST be at end of stage1
; layout of this block used by setup code (stage1.py)

    ; ss:sp
    conf_stack_ofs dw 0
    conf_stack_seg dw 0

    ; where to place stage2
    conf_stage2_ofs dw 0
    conf_stage2_seg dw 0

    ; stage2 entry point
    conf_entry_ofs dw 0
    conf_entry_seg dw 0

    ; LBA of the first blocklist sector
    conf_blocklist_lba dq 0

; === end of configuration block ===
