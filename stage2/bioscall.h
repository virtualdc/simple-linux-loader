#ifndef BIOSCALL_H
#define BIOSCALL_H

#include <inttypes.h>


/* MUST have same layout as struc registers in bioscall.asm */
#pragma pack(push, 1)
struct registers
{
    union {
        uint32_t eax;
        struct {
            uint16_t ax;
            uint16_t pad1;
        };
    };
    union {
        uint32_t ebx;
        struct {
            uint16_t bx;
            uint16_t pad2;
        };
    };
    union {
        uint32_t ecx;
        struct {
            uint16_t cx;
            uint16_t pad3;
        };
    };
    union {
        uint32_t edx;
        struct {
            uint16_t dx;
            uint16_t pad4;
        };
    };
    uint16_t di;
    uint16_t si;
    uint16_t ds;
    uint16_t es;
    uint16_t flags;
};
#pragma pack(pop)


/*
    - sets registers as described in regs
    - calls interupt int_id
    - saves result registers into regs
*/
void bios_call(struct registers * regs, uint32_t int_id);


/*
    - switches off protected mode
    - passes control to kernel entry point
*/
void launch_kernel(uint8_t * realmode_offset);

#endif
