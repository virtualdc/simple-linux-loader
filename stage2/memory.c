#include "memory.h"
#include "bioscall.h"


uint32_t get_low_memory_limit()
{
    struct registers regs;
    bios_call(&regs, 0x12);
    return regs.ax * 1024;
}
