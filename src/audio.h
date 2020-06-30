#pragma once

#include "ram.h"


class Audio
{
public:
    void init();
    void callback(float* stream, int length);

    class FrequencySweep
    {
    public:
        int div = 0;

        int sweep_shift = 0;
        bool sweep_sub = false;
        int sweep_delay = 0;

        int sweep_counter = 0;

        bool update();
    };
    class Length
    {
    public:
        bool enabled = false;
        int counter = 0;

        bool update();
    };
    class VolumeEnvelope
    {
    public:
        int value = 0;
        bool sweep_inc = false;
        int sweep_delay = 0;
        int sweep_counter = 0;

        bool update();
    };

    class NR10Reg : public Mem8
    {
    public:
        uint8_t get() const override;
        void setImpl(uint8_t value) override;
    };
    class NRx1Reg : public Mem8
    {
    public:
        NRx1Reg(Length& length, uint8_t mask) : length(length), mask(mask) {}
        uint8_t get() const override;
        void setImpl(uint8_t value) override;
    private:
        Length& length;
        uint8_t mask;
    };
    class NRx2Reg : public Mem8
    {
    public:
        NRx2Reg(VolumeEnvelope& env) : env(env) {}
        uint8_t get() const override;
        void setImpl(uint8_t value) override;

    private:
        VolumeEnvelope& env;
    };
    class NRx3Reg : public Mem8
    {
    public:
        NRx3Reg(int& div) : div(div) {}
        uint8_t get() const override;
        void setImpl(uint8_t value) override;
    private:
        int& div;
    };
    class NRx4Reg : public Mem8
    {
    public:
        NRx4Reg(bool& active, Length& length)
        : active(active), length(length) {}
        NRx4Reg(bool& active, Length& length, int& frequency_div)
        : active(active), length(length), frequency_div(&frequency_div) {}

        uint8_t get() const override;
        void setImpl(uint8_t value) override;
    private:
        bool& active;
        Length& length;
        int* frequency_div = nullptr;
    };
    class NR52Reg : public Mem8
    {
    public:
        uint8_t value;
        uint8_t get() const override;
        void setImpl(uint8_t value) override { this->value = value & 0x80; }
    };
    class SoundChannel
    {
    public:
        bool active = false;
        int wave_counter = 0;
        FrequencySweep frequency;
        VolumeEnvelope volume;
        Length length;

    protected:
        void update();
    private:
        int state = 0;
    };
    class SquareWaveSoundChannel : public SoundChannel
    {
    public:
        void callback(float* stream, int length);
    };
    class WaveSoundChannel : public SoundChannel
    {
    public:
        void callback(float* stream, int length);
    };
    class NoiseSoundChannel : public SoundChannel
    {
    public:
        void callback(float* stream, int length);
    private:
        uint32_t lfsr = 0xFFFF;
    };
    SquareWaveSoundChannel square_1;
    SquareWaveSoundChannel square_2;
    WaveSoundChannel wave;
    NoiseSoundChannel noise;

    NR10Reg NR10;
    NRx1Reg NR11{square_1.length, 0x3F};
    NRx2Reg NR12{square_1.volume};
    NRx3Reg NR13{square_1.frequency.div};
    NRx4Reg NR14{square_1.active, square_1.length, square_1.frequency.div};
    NRx1Reg NR21{square_2.length, 0x3F};
    NRx2Reg NR22{square_2.volume};
    NRx3Reg NR23{square_2.frequency.div};
    NRx4Reg NR24{square_2.active, square_2.length, square_2.frequency.div};
    Mem8Ram NR30;
    NRx1Reg NR31{wave.length, 0xFF};
    Mem8Ram NR32;
    NRx3Reg NR33{wave.frequency.div};
    NRx4Reg NR34{wave.active, wave.length, wave.frequency.div};
    NRx1Reg NR41{noise.length, 0x3F};
    NRx2Reg NR42{noise.volume};
    Mem8Ram NR43;
    NRx4Reg NR44{noise.active, noise.length};
    Mem8Ram NR50;
    Mem8Ram NR51;
    NR52Reg NR52;
    Mem8Ram WAVE[16];
};

extern Audio audio;
