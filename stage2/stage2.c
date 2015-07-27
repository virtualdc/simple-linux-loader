#include <inttypes.h>
#include <stddef.h>
#include "bioscall.h"
#include "console.h"
#include "disk.h"


/* MUST have same layout with entry.asm and stage2.py */
#pragma pack(push, 1)
struct stage2_header
{
    uint16_t size;
    uint64_t kernel_blocklist_lba;
    uint64_t initrd_blocklist_lba;
    char command_line[256];
};
#pragma pack(pop)


struct kernel
{
    uint8_t * realmode_part;
    size_t realmode_size;
    uint8_t * protmode_part;
    size_t protmode_size;
};


static uint32_t get_low_memory_limit()
{
    struct registers regs;
    bios_call(&regs, 0x12);
    return regs.ax * 1024;
}


static int load_realmode_part(struct blocklist * list, uint8_t * ptr, size_t * size)
{
    *size = 0;

    /* load first sector of the kernel */
    uint64_t lba;
    int ret = get_next_sector(list, &lba);
    if (ret)
        return ret;

    ret = read_sector(list->disk, lba, ptr);
    if (ret)
        return ret;

    /* get RM part size in sectors */
    size_t sectors = ptr[0x01F1];
    if (sectors == 0)
        sectors = 4;

    /* load remaining sectors */
    *size += SECTOR_SIZE;
    for (size_t i = 0; i < sectors; ++i)
    {
        ptr += SECTOR_SIZE;
        *size += SECTOR_SIZE;
        ret = get_next_sector(list, &lba);
        if (ret)
            return ret;
        ret = read_sector(list->disk, lba, ptr);
        if (ret)
            return ret;
    }

    return 0;
}


static int load_protmode_part(struct blocklist * list, uint8_t * ptr, size_t * size)
{
    *size = 0;
    while (1)
    {
        uint64_t lba;
        int ret = get_next_sector(list, &lba);
        if (ret)
            return ret;
        if (lba + 1 == 0)
            return 0;
        ret = read_sector(list->disk, lba, ptr);
        if (ret)
            return ret;
        ptr += SECTOR_SIZE;
        *size += SECTOR_SIZE;
    }
}


static int load_kernel(uint32_t disk, uint64_t lba, struct kernel * out)
{
    struct blocklist b;
    int ret = init_blocklist(disk, lba, &b);
    if (ret)
        return ret;

    /* load RM part to 64kb below low memory limit */
    uint32_t limit = get_low_memory_limit();
    put_format("low memory limit: %d\r\n", limit);
    out->realmode_part = (uint8_t*)(limit - 0x10000);

    ret = load_realmode_part(&b, out->realmode_part, &out->realmode_size);
    if (ret)
        return ret;

    /* load PM part just above ISA memory hole at 0x1000000 */
    out->protmode_part = (uint8_t*)(0x1000000);

    ret = load_protmode_part(&b, out->protmode_part, &out->protmode_size);
    if (ret)
        return ret;

    /* display some info */
    put_format("RM loaded at %d size %d\r\n", (uint32_t)out->realmode_part, out->realmode_size);
    put_format("PM loaded at %d size %d\r\n", (uint32_t)out->protmode_part, out->protmode_size);

    return 0;
}


static void die()
{
    while (1);
}


void stage2_main(uint32_t drive_num, struct stage2_header * header)
{
    /* show params */
    put_string("Stage2 started:\r\n");
    put_format("  drive_num=%b\r\n", drive_num);
    put_format("  kernel=%q\r\n", header->kernel_blocklist_lba);
    put_format("  initrd=%q\r\n", header->initrd_blocklist_lba);
    put_format("  cmdline=\"%s\"\r\n", header->command_line);

    /* load kernel */
    struct kernel kernel;
    int ret = load_kernel(drive_num, header->kernel_blocklist_lba, &kernel);
    if (ret)
    {
        put_format("Can't load kernel: %d\r\n", ret);
        die();
    }

}