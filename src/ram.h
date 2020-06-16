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

    void setImpl(uint8_t value) override
    {
        this->value = value;
    }
};

class Ram
{
public:
    void init();
    Mem8& getWRam(uint16_t address);
    Mem8& getHRam(uint16_t address);

    Mem8Ram SVBK;
};

extern Ram ram;
