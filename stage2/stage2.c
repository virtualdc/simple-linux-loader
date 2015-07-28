#include <inttypes.h>
#include <stddef.h>
#include "bioscall.h"
#include "console.h"
#include "disk.h"
#include "memory.h"



/* MUST have same layout with entry.asm and stage2.py */
#define COMMAND_LINE_SIZE 256

#pragma pack(push, 1)
struct stage2_header
{
    uint16_t size;
    uint64_t kernel_blocklist_lba;
    uint64_t initrd_blocklist_lba;
    uint32_t kernel_size;
    uint32_t initrd_size;
    char command_line[COMMAND_LINE_SIZE];
};
#pragma pack(pop)


struct memory_range
{
    uint8_t * start;
    size_t size;
};


struct kernel_info
{
    struct memory_range realmode;
    struct memory_range protmode;
    struct memory_range initrd;
};


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


static int load_kernel(uint32_t disk, uint64_t lba, struct kernel_info * out)
{
    struct blocklist b;
    int ret = init_blocklist(disk, lba, &b);
    if (ret)
        return ret;

    /* load RM part to 64kb below low memory limit */
    uint32_t limit = get_low_memory_limit();
    put_format("low memory limit: %d\r\n", limit);
    out->realmode.start = (uint8_t*)(limit - 0x10000);

    ret = load_realmode_part(&b, out->realmode.start, &out->realmode.size);
    if (ret)
        return ret;

    /* load PM part just above ISA memory hole at 0x1000000 */
    out->protmode.start = (uint8_t*)(0x1000000);

    ret = load_protmode_part(&b, out->protmode.start, &out->protmode.size);
    if (ret)
        return ret;


    return 0;
}


static int load_initrd(uint32_t disk, uint64_t lba, struct kernel_info * info)
{
    struct blocklist b;
    int ret = init_blocklist(disk, lba, &b);
    if (ret)
        return ret;

    /* load initrd to some high position in upper memory */
    /* TODO: use memory map to detect this location  */
    info->initrd.start = (uint8_t*)0x4000000;
    info->initrd.size = 0;

    /* load sectors */
    uint8_t * ptr = info->initrd.start;
    while (1)
    {
        uint64_t lba;
        int ret = get_next_sector(&b, &lba);
        if (ret)
            return ret;
        if (lba + 1 == 0)
            return 0;
        ret = read_sector(disk, lba, ptr);
        if (ret)
            return ret;
        ptr += SECTOR_SIZE;
        info->initrd.size += SECTOR_SIZE;
    }
}


static int configure_kernel(struct kernel_info * info, const char * cmd)
{
    uint8_t * p = info->realmode.start;

    uint8_t * cmdline = info->realmode.start + 0x10000 - COMMAND_LINE_SIZE;
    for (size_t i = 0; i < COMMAND_LINE_SIZE; ++i)
        cmdline[i] = cmd[i];

    *(uint16_t*)(p+0x1FA) = 0x303; // vid_mode = 800x600 256
    p[0x210] = 0xFF; // loader_type = unknown loader
    p[0x211] = 0x81; // loadflags = can use heap | loaded high
    *(uint32_t*)(p+0x214) = (uintptr_t)info->protmode.start; // code32_start
    *(uint32_t*)(p+0x218) = (uintptr_t)info->initrd.start; // initrd
    *(uint32_t*)(p+0x21C) = info->initrd.size;
    *(uint16_t*)(p+0x224) = 0x10000 - 0x200 - COMMAND_LINE_SIZE; // heap_end_ptr
    *(uint32_t*)(p+0x228) = (uintptr_t)cmdline; // cmd_line_ptr

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
    put_format("  kernel=%q size=%d\r\n", header->kernel_blocklist_lba, header->kernel_size);
    put_format("  initrd=%q size=%d\r\n", header->initrd_blocklist_lba, header->initrd_size);
    put_format("  cmdline=\"%s\"\r\n", header->command_line);

    struct kernel_info info;

    /* load kernel */
    int ret = load_kernel(drive_num, header->kernel_blocklist_lba, &info);
    if (ret)
    {
        put_format("Can't load kernel: %d\r\n", ret);
        die();
    }
    put_format("RM loaded at %d size %d\r\n", (uint32_t)info.realmode.start, info.realmode.size);
    put_format("PM loaded at %d size %d\r\n", (uint32_t)info.protmode.start, info.protmode.size);

    /* load initrd */
    ret = load_initrd(drive_num, header->initrd_blocklist_lba, &info);
    if (ret)
    {
        put_format("Can't load initrd: %d\r\n", ret);
        die();
    }
    put_format("initrd loaded at %d size %d\r\n", (uint32_t)info.initrd.start, info.initrd.size);

    /* configure kernel */
    ret = configure_kernel(&info, header->command_line);
    if (ret)
    {
        put_format("Can't configure kernel: %d\r\n", ret);
        die();
    }
    put_string("kernel configured\r\n");

    /* pass control to kernel */
    put_string("Passing control to the kernel...\r\n");
    launch_kernel(info.realmode.start);
}
