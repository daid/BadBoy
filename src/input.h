#pragma once

#include "mem8.h"

class Input : public Mem8
{
public:
    virtual uint8_t get() const override;
    virtual void set(uint8_t) override;

    void update();

    bool quit = false;
private:
    uint8_t directions = 0x10;
    uint8_t buttons = 0x20;

    enum class Mode
    {
        None,
        Buttons,
        Directions,
    } mode = Mode::None;
};

extern Input input;
