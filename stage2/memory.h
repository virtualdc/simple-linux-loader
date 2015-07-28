#ifndef MEMORY_H
#define MEMORY_H

#include <inttypes.h>


uint32_t get_low_memory_limit();


uint16_t segment_of(void * p);
uint16_t offset_of(void * p);


#define MEMORY_MAP_USABLE 1
#define MEMORY_MAP_RESERVED 2
#define MEMORY_MAP_ACPI_RECLAIMABLE 3
#define MEMORY_MAP_ACPI_NVS 4
#define MEMORY_MAP_BAD 5


struct memory_map_entry
{
    uint64_t address;
    uint64_t size; // 0 - ignore entry
    uint32_t type; // one of MEMORY_MAP_*
    uint32_t ext;
};


/*
    token - opaque value that passed between calls
*/
int get_first_memory_map_entry(uint32_t * token, struct memory_map_entry * entry);
int get_next_memory_map_entry(uint32_t * token, struct memory_map_entry * entry);



#endif