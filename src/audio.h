#pragma once

#include "ram.h"


class Audio
{
public:
    class NR52Reg : public Mem8
    {
    public:
        uint8_t get() const override { return 0x00; }
        void setImpl(uint8_t value) override {}
    };

    Mem8Ram NR10;
    Mem8Ram NR11;
    Mem8Ram NR12;
    Mem8Ram NR13;
    Mem8Ram NR14;
    Mem8Ram NR21;
    Mem8Ram NR22;
    Mem8Ram NR23;
    Mem8Ram NR24;
    Mem8Ram NR30;
    Mem8Ram NR31;
    Mem8Ram NR32;
    Mem8Ram NR33;
    Mem8Ram NR34;
    Mem8Ram NR41;
    Mem8Ram NR42;
    Mem8Ram NR43;
    Mem8Ram NR44;
    Mem8Ram NR50;
    Mem8Ram NR51;
    NR52Reg NR52;
    Mem8Ram WAVE[16];
};

extern Audio audio;
