#include "ram.h"
#include "cpu.h"
#include <stdio.h>

Ram ram;

Mem8Ram storage_wram[0x8000];
Mem8Ram storage_hram[0x0080];

void Ram::init()
{
    for(uint32_t n=0; n<0x8000; n++)
        storage_wram[n].id = n | ID_WRAM;
    for(uint32_t n=0; n<0x0080; n++)
        storage_hram[n].id = n | ID_HRAM;
}

Mem8& Ram::getWRam(uint16_t address)
{
    if (address >= 0x1000 && cpu.gbc && (SVBK.value & 0x07))
        return storage_wram[(address & 0x0FFF) | (0x1000 * (SVBK.value & 0x07))];
    return storage_wram[address];
}

Mem8& Ram::getHRam(uint16_t address)
{
    return storage_hram[address];
}
