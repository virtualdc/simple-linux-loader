#include "disk.h"
#include "bioscall.h"
#include <stddef.h>


struct disk_address_packet
{
    uint8_t size;
    uint8_t padding;
    uint16_t sectors;
    uint16_t offset;
    uint16_t segment;
    uint64_t lba;
};


static uint16_t segment_of(void * p)
{
    uintptr_t ptr = (uintptr_t)p;
    return (ptr >> 4) & 0xFFFF;
}


static uint16_t offset_of(void * p)
{
    uintptr_t ptr = (uintptr_t)p;
    return ptr & 0x0000F;
}


int read_sector(uint32_t disk, uint64_t lba, void * buf)
{
    // stack located in low memory, so we can access buf & dap in RM
    char tmpbuf[SECTOR_SIZE];

    struct disk_address_packet dap;
    dap.size = sizeof(dap);
    dap.padding = 0;
    dap.sectors = 1;
    dap.offset = offset_of(&tmpbuf);
    dap.segment = segment_of(&tmpbuf);
    dap.lba = lba;

    struct registers regs;
    regs.ax = 0x4200;
    regs.dx = disk & 0xFF;
    regs.ds = segment_of(&dap);
    regs.si = offset_of(&dap);
    bios_call(&regs, 0x13);

    if (regs.flags & 1) {
        return regs.ax >> 8;
    }

    for (size_t i = 0; i < SECTOR_SIZE; ++i)
        ((char*)buf)[i] = tmpbuf[i];

    return 0;
}
