#pragma once

#include "mem8.h"

class Input : public Mem8
{
public:
    virtual uint8_t get() const override;
    virtual void setImpl(uint8_t) override;

    void update();

    bool quit = false;
private:
    uint8_t directions = 0x00;
    uint8_t buttons = 0x00;
    uint8_t mode = 0xFF;
};

extern Input input;
