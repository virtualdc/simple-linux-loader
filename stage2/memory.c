#include "memory.h"
#include "bioscall.h"


uint32_t get_low_memory_limit()
{
    struct registers regs;
    memset(&regs, 0, sizeof(regs));
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


static int get_memory_map_entry(uint32_t * token, struct memory_map_entry * entry)
{
    struct memory_map_entry buf;
    struct registers regs;

    memset(&regs, 0, sizeof(regs));

    regs.eax = 0xE820;
    regs.ebx = *token;
    regs.ecx = sizeof(struct memory_map_entry);
    regs.edx = 0x534D4150;
    regs.es = segment_of(&buf);
    regs.di = offset_of(&buf);

    bios_call(&regs, 0x15);
    if ((regs.flags & 1) != 0) /* CF set - error */
        return 1;
    if (regs.eax != 0x534D4150)
        return 2;

    *token = regs.ebx;
    entry->address = buf.address;
    entry->size = buf.size;
    entry->type = buf.type;
    entry->ext = buf.ext;

    return 0;
}


int get_first_memory_map_entry(uint32_t * token, struct memory_map_entry * entry)
{
    *token = 0;
    return get_memory_map_entry(token, entry);
}


int get_next_memory_map_entry(uint32_t * token, struct memory_map_entry * entry)
{
    /* if memory map cycles to beginning - return error to stop enumeration */
    if (*token == 0)
        return 1;
    return get_memory_map_entry(token, entry);
}


void * memset(void *s, int c, size_t n)
{
    for (size_t i = 0; i < n; ++i)
        ((char*)s)[i] = c;
    return s;
}