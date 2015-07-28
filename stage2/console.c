#include "console.h"
#include "bioscall.h"
#include <stddef.h>
#include <stdarg.h>


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


static void put_hex(uint64_t value, size_t count)
{
    for (size_t i = 0; i < count; ++i)
    {
        char c = (value >> ((count - 1 - i) * 4)) & 15;
        put_char(c >= 10 ? 'A' + c - 10 : '0' + c);
    }
}


void put_format(const char * s, ...)
{
    va_list list;
    va_start(list, s);
    while (*s)
    {
        char c = *s++;
        if (c != '%')
        {
            put_char(c);
            continue;
        }
        if (*s)
        {
            switch (*s++)
            {
            case 'b':
                put_hex(va_arg(list, uint32_t), 2);
                break;
            case 'w':
                put_hex(va_arg(list, uint32_t), 4);
                break;
            case 'd':
                put_hex(va_arg(list, uint32_t), 8);
                break;
            case 'q':
                put_hex(va_arg(list, uint64_t), 16);
                break;
            case 's':
                put_string(va_arg(list, char *));
                break;
            }
        }
    }
}