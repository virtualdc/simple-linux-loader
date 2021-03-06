#include <inttypes.h>
#include <stddef.h>
#include "bioscall.h"
#include "console.h"
#include "disk.h"
#include "memory.h"


#define PAGE_SIZE 4096


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


uint8_t * choose_address_for_initrd(uint32_t initrd_size, uint32_t initrd_addr_max)
{
    uint32_t token;
    struct memory_map_entry entry;

    /* round initrd size to page boundary */
    if (initrd_size % PAGE_SIZE != 0)
        initrd_size = ((initrd_size / PAGE_SIZE) + 1) * PAGE_SIZE;

    int ret = get_first_memory_map_entry(&token, &entry);
    if (ret)
        return 0;

    uint32_t choosen = 0;

    do
    {
        /* skip unusable */
        if (entry.type != MEMORY_MAP_USABLE)
            continue;

        uint64_t start = entry.address;
        uint64_t end = entry.address + entry.size - 1;

        /* initrd must be located in upper memory */
        if (start < 0x100000)
            start = 0x100000;

        /* but below max address, specified by kernel */
        if (end > initrd_addr_max)
            end = initrd_addr_max;

        /* align to page size */
        if (start % PAGE_SIZE != 0)
            start = ((start / PAGE_SIZE) + 1) * PAGE_SIZE;
        if (end % PAGE_SIZE != PAGE_SIZE - 1)
            end = (end / PAGE_SIZE) * PAGE_SIZE - 1;

        /* range must be valid */
        if (start >= end)
            continue;

        /* initrd must fit into range */
        if (initrd_size > end - start)
            continue;

        uint32_t addr = end - initrd_size + 1;
        put_format("Candidate at %d in range %q-%q\r\n", addr, start, end);

        /* choose highest region */
        if (addr > choosen)
            choosen = addr;

    } while (get_next_memory_map_entry(&token, &entry) == 0);

    return (uint8_t*)choosen;
}



static int load_initrd(uint32_t disk, uint64_t lba, uint32_t size, struct kernel_info * info)
{
    struct blocklist b;
    int ret = init_blocklist(disk, lba, &b);
    if (ret)
        return ret;

    uint32_t initrd_addr_max = *(uint32_t*)(info->realmode.start+0x22c);
    put_format("Last initrd byte allowed by kernel: %d\r\n", initrd_addr_max);

    /* load initrd to some high position in upper memory */
    /* TODO: use memory map to detect this location  */
    info->initrd.start = choose_address_for_initrd(size, initrd_addr_max);
    if (!info->initrd.start) {
        put_string("Can't choose address for initrd\r\n");
        return 1;
    }
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


static int show_memory_map()
{
    uint32_t token;
    struct memory_map_entry entry;

    put_string("Memory map:\r\n");

    int ret = get_first_memory_map_entry(&token, &entry);
    if (ret)
        return ret;

    do
    {
        put_format("  %q %q %d\r\n", entry.address, entry.size, entry.type);
    } while (get_next_memory_map_entry(&token, &entry) == 0);

    return 0;
}


void stage2_main(uint32_t drive_num, struct stage2_header * header)
{
    /* show params */
    put_string("Stage2 started:\r\n");
    put_format("  drive_num=%b\r\n", drive_num);
    put_format("  kernel=%q size=%d\r\n", header->kernel_blocklist_lba, header->kernel_size);
    put_format("  initrd=%q size=%d\r\n", header->initrd_blocklist_lba, header->initrd_size);
    put_format("  cmdline=\"%s\"\r\n", header->command_line);

    /* show memory map */
    int ret = show_memory_map();
    if (ret)
    {
        put_format("Can't show memory map: %d\r\n", ret);
        die();
    }

    struct kernel_info info;

    /* load kernel */
    ret = load_kernel(drive_num, header->kernel_blocklist_lba, &info);
    if (ret)
    {
        put_format("Can't load kernel: %d\r\n", ret);
        die();
    }
    put_format("RM loaded at %d size %d\r\n", (uint32_t)info.realmode.start, info.realmode.size);
    put_format("PM loaded at %d size %d\r\n", (uint32_t)info.protmode.start, info.protmode.size);

    /* load initrd */
    ret = load_initrd(drive_num, header->initrd_blocklist_lba, header->initrd_size, &info);
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
