#include "ram.h"
#include <stdio.h>


Mem8Ram storage_wram[0x8000];
Mem8Ram storage_hram[0x080];

Mem8& wram::get(uint16_t address)
{
    return storage_wram[address];
}

Mem8& hram::get(uint16_t address)
{
    return storage_hram[address];
}
