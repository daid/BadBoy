#pragma once

#include "mem8.h"

class Card
{
public:
    void init();

    Mem8& getRom(uint16_t address);
    Mem8& getSRam(uint16_t address);
    Mem8& getBoot(uint16_t address);

    int upper_bank = 0x01;
};
extern Card card;
