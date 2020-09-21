#pragma once

#include "mem8.h"
#include "mbc.h"
#include <memory>

class Card
{
public:
    void init();
    bool load(const char* filename);

    Mem8& getRom(uint16_t address);
    Mem8& getSRam(uint16_t address);
    Mem8& getBoot(uint16_t address);

    std::unique_ptr<MBC> mbc;

    void dumpInstrumentation(FILE* f);
};
extern Card card;
