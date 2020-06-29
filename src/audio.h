#pragma once

#include "ram.h"


class Audio
{
public:
    void init();
    void callback(float* stream, int length);

    class NR52Reg : public Mem8
    {
    public:
        uint8_t value;
        uint8_t get() const override { return value; }
        void setImpl(uint8_t value) override { this->value = value & 0x80; }
    };
    class SoundChannel
    {
    public:
        void callback(float* stream, int length);

        // settings
        bool active = false;
        int freq_div = 0;
        int length = 0;
        int duty = 0;
        int freq_sweep_shift = 0;
        bool freq_sweep_inc = false;
        int freq_sweep_delay = 0;
        int volume = 0;
        bool volume_sweep_inc = false;
        int volume_sweep_delay = 0;

        // runtime values
        int wave_counter = 0;
        int freq_sweep_counter = 0;
        int volume_sweep_counter = 0;

        int state = 0;
    };
    SoundChannel square_1;
    SoundChannel square_2;
    SoundChannel wave;
    SoundChannel noise;

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
