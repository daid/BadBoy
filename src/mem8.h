#pragma once

#include <stdint.h>

class Mem8
{
public:
    virtual uint8_t get() const = 0;
    virtual void set(uint8_t) = 0;
};
