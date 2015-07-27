#include "bioscall.h"

void put_char(char c)
{
    struct registers regs;
    regs.ax = 0x0E00 | (unsigned char)c;
    regs.bx = 0x0000;
    bios_call(&regs, 0x10);
}


void put_string(const char * s)
{
    while (*s)
    {
        put_char(*s);
        ++s;
    }
}
