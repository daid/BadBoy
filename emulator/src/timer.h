#pragma once

#include "mem8.h"

class Timer
{
public:
    class DivReg : public Mem8
    {
    public:
        uint8_t get() const override;
        void setImpl(uint8_t) override;
    private:
        uint32_t offset = 0;
    };
    class BasicReg : public Mem8
    {
    public:
        uint8_t value;
        uint8_t get() const override;
        void setImpl(uint8_t) override;
    };

    DivReg DIV;
    BasicReg TIMA;
    BasicReg TMA;
    BasicReg TAC;
    uint32_t timer_tick_cycle;

    void update();
};

extern Timer timer;
