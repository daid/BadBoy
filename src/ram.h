#pragma once

#include "mem8.h"

class Mem8Ram : public Mem8
{
public:
    uint8_t value;

    uint8_t get() const override
    {
        return value;
    }

    void set(uint8_t value) override
    {
        this->value = value;
    }
};

namespace wram
{
    Mem8& get(uint16_t address);
}

namespace hram
{
    Mem8& get(uint16_t address);
}
