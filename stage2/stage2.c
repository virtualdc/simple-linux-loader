#include <inttypes.h>
#include "bioscall.h"
#include "console.h"


void stage2_main(uint32_t drive_num)
{
    put_string("Stage2 started.\r\n");
    put_format("  drive_num=%b\r\n", drive_num);
    // TODO: load linux :)
}