#include "ram.h"
#include "cpu.h"
#include <stdio.h>

Ram ram;

static Mem8Block<Mem8Ram> storage_wram;
static Mem8Block<Mem8Ram> storage_hram;

void Ram::init()
{
    storage_wram.resize(0x8000);
    storage_hram.resize(0x0080);
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

void Ram::dumpInstrumentation(FILE* f)
{
    storage_wram.dumpInstrumentation(f);
    storage_hram.dumpInstrumentation(f);
}
