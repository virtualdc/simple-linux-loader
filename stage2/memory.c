#include "memory.h"
#include "bioscall.h"


uint32_t get_low_memory_limit()
{
    struct registers regs;
    bios_call(&regs, 0x12);
    return regs.ax * 1024;
}


uint16_t segment_of(void * p)
{
    uintptr_t ptr = (uintptr_t)p;
    return (ptr >> 4) & 0xFFFF;
}


uint16_t offset_of(void * p)
{
    uintptr_t ptr = (uintptr_t)p;
    return ptr & 0x0000F;
}
