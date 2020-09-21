#pragma once

#include "mem8.h"

class Input : public Mem8
{
public:
    virtual uint8_t get() const override;
    virtual void setImpl(uint8_t) override;

    void setReplayFile(const char* filename, bool playback);
    void update();

    bool quit = false;
    int fast_forward = 0;
private:
    FILE* replay_file = nullptr;
    bool replay_playback = false;

    uint8_t directions = 0x00;
    uint8_t buttons = 0x00;
    uint8_t mode = 0xFF;
};

extern Input input;
