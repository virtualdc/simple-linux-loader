#include <inttypes.h>
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


void stage2_main(uint32_t drive_num, struct stage2_header * header)
{
    put_string("Stage2 started.\r\n");
    put_format("  drive_num=%b\r\n", drive_num);
    put_format("  kernel=%q\r\n", header->kernel_blocklist_lba);
    put_format("  initrd=%q\r\n", header->initrd_blocklist_lba);
    put_format("  cmdline=\"%s\"\r\n", header->command_line);
    // TODO: load linux :)
}