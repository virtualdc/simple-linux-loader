#ifndef MEMORY_H
#define MEMORY_H

#include <inttypes.h>


uint32_t get_low_memory_limit();


uint16_t segment_of(void * p);
uint16_t offset_of(void * p);


#endif