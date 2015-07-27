#ifndef DISK_H
#define DISK_H

#include <inttypes.h>


#define SECTOR_SIZE 512


/*
    read sector into buffer
    returns 0 on success, errcode on failure
*/
int read_sector(uint32_t disk, uint64_t lba, void * buf);


#endif