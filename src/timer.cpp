#include <stdio.h>
#include "timer.h"
#include "cpu.h"

Timer timer;

uint8_t Timer::DivReg::get() const
{
    return cpu.cycles >> 8;
}

void Timer::DivReg::set(uint8_t value)
{
}

uint8_t Timer::BasicReg::get() const
{
    return value;
}

void Timer::BasicReg::set(uint8_t value)
{
    this->value = value;
}

void Timer::update()
{
    if (TAC.value & 0x04)
    {
        uint32_t interval = 1024;
        switch(TAC.value & 0x03)
        {
        case 0: interval = 1024; break;
        case 1: interval = 16; break;
        case 2: interval = 64; break;
        case 3: interval = 256; break;
        }
        if (cpu.cycles - timer_tick_cycle >= interval)
        {
            timer_tick_cycle += interval;
            if (TIMA.value == 0xFF)
            {
                TIMA.value = TMA.value;
                cpu.setInterrupt(0x04);
            }
            else
            {
                TIMA.value += 1;
            }
        }
    }
    else
    {
        timer_tick_cycle = cpu.cycles;
    }
}
