bits 32

global bios_call:function
global launch_kernel:function

section .bioscall

; MUST have same layout as struct registers in bioscall.h
struc registers
    .regAX resw 1
    .regBX resw 1
    .regCX resw 1
    .regDX resw 1
    .regDI resw 1
    .regSI resw 1
    .regDS resw 1
    .regES resw 1
    .regFLAGS resw 1
endstruc


; void bios_call(struct registers * regs, uint32_t int_id);

bios_call:

    push ebp
    mov ebp, esp

    ; save registers that will be modified
    pushfd
    push eax
    push ebx
    push ecx
    push edx
    push edi
    push esi
    push ds
    push es
    push fs
    push gs

    ; load parameters
    mov eax, [ebp + 12] ; int_id
    mov esi, [ebp + 8] ; regs

    ; push return address and flags (for iret in interrupt handler)
    push word [esi + registers.regFLAGS]
    push word 0
    push word .return_from_int

    ; find and push interrupt handler address (for retf to enter handler)
    push word [eax * 4 + 2]
    push word [eax * 4 + 0]

    ; push desired register values (will be popped later in RM)
    push word [esi + registers.regFLAGS]
    push word [esi + registers.regAX]
    push word [esi + registers.regBX]
    push word [esi + registers.regCX]
    push word [esi + registers.regDX]
    push word [esi + registers.regDI]
    push word [esi + registers.regSI]
    push word [esi + registers.regDS]
    push word [esi + registers.regES]

    ; jump to 16-bit segment
    jmp 0x20 : .switch_to_16_bit

bits 16
.switch_to_16_bit:

    ; reload segment registers
    mov ax, 0x28
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax

    ; disable protected mode
    mov eax, cr0
    and al, 0xFE
    mov cr0, eax

    ; jump to real mode
    jmp 0x0000 : .switch_to_real

.switch_to_real:

    ; set SP
    xor ax, ax
    mov ss, ax

    ; pop desired register values
    pop es
    pop ds
    pop si
    pop di
    pop dx
    pop cx
    pop bx
    pop ax
    popf

    ; enable interrupts
    sti

    ; go to the interrupt handler
    retf

.return_from_int:

    ; disable interrupts
    cli

    ; we just returned from interrupt handler
    ; push modified register values
    pushf
    push ax
    push bx
    push cx
    push dx
    push di
    push si
    push ds
    push es

    ; enable protected mode
    mov eax, cr0
    or al, 1
    mov cr0, eax

    ; jump to protected mode
    jmp 0x10 : .switch_to_prot

bits 32
.switch_to_prot:

    ; reload segment registers
    mov ax, 0x18
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax

    ; pop output values
    mov esi, [ebp + 8] ; regs
    pop word [esi + registers.regES]
    pop word [esi + registers.regDS]
    pop word [esi + registers.regSI]
    pop word [esi + registers.regDI]
    pop word [esi + registers.regDX]
    pop word [esi + registers.regCX]
    pop word [esi + registers.regBX]
    pop word [esi + registers.regAX]
    pop word [esi + registers.regFLAGS]

    ; restore registers
    pop gs
    pop fs
    pop es
    pop ds
    pop esi
    pop edi
    pop edx
    pop ecx
    pop ebx
    pop eax
    popfd
    pop ebp

    ret


; void launch_kernel(uint8_t * realmode_offset);

launch_kernel:

    ; yes, we can use [esp] in 32-bit addressing mode :)
    mov ebx, [esp + 4]

    ; calculate segment (cx) and offset (bx) of RM part
    mov ecx, ebx
    and ebx, 15
    shr ecx, 4

    ; jump to 16-bit segment
    jmp 0x20 : .switch_to_16_bit

bits 16
.switch_to_16_bit:

    ; reload segment registers
    mov ax, 0x28
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax

    ; disable protected mode
    mov eax, cr0
    and al, 0xFE
    mov cr0, eax

    ; jump to real mode
    jmp 0x0000 : .switch_to_real

.switch_to_real:

    ; we are in real mode now
    ; set all segment registers to start of kernel's RM part
    mov ds, cx
    mov es, cx
    mov fs, cx
    mov gs, cx
    mov ss, cx

    ; setup stack pointer 256 bytes below end of segment
    mov sp, 0xFF00

    ; jump to kernel's entry point (0x200 from start)
    add cx, 0x20
    push cx
    push bx
    retf
