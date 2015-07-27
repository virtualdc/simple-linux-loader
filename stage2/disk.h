#ifndef DISK_H
#define DISK_H

#include <inttypes.h>


#define SECTOR_SIZE 512


/*
    read sector into buffer
    returns 0 on success, errcode on failure
*/
int read_sector(uint32_t disk, uint64_t lba, void * buf);



struct blocklist
{
    uint64_t sectors[SECTOR_SIZE / sizeof(uint64_t)];
    uint32_t offset;
    uint32_t disk;
};


/*
    loads first sector into buffer
    returns 0 on success, errcode on failure
*/
int init_blocklist(uint32_t disk, uint64_t lba, struct blocklist * list);


/*
    puts lba of the next data sector into *lba
    reads next blocklist sector if required
    returns 0 on success, errcode on failure
*/
int get_next_sector(struct blocklist * list, uint64_t * lba);


#endif