#pragma once

#include "mem8.h"

class Card
{
public:
    void init(const char* filename);

    Mem8& getRom(uint16_t address);
    Mem8& getSRam(uint16_t address);
    Mem8& getBoot(uint16_t address);

    int rom_upper_bank = 0x01;
    int ram_bank = 0x00;

    void dumpInstrumentation(FILE* f);
};
extern Card card;
