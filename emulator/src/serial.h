#pragma once

#include "mem8.h"


class Serial
{
public:
    class SBReg : public Mem8
    {
        uint8_t get() const override;
        void setImpl(uint8_t value) override;
    };
    class SCReg : public Mem8
    {
        uint8_t get() const override;
        void setImpl(uint8_t value) override;
    };

    SBReg SB;
    SCReg SC;

    uint8_t data = 0;
    int transfer_bits_left = 0;
    uint32_t start_cycle = 0;
    uint32_t bit_transfer_cycles = 512;

    void update();
};
extern Serial serial;