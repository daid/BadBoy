#include "audio.h"
#include <SDL.h>


Audio audio;
static SDL_AudioDeviceID audio_device;
class LockAudio
{
public:
    LockAudio() { SDL_LockAudioDevice(audio_device); }
    ~LockAudio() { SDL_UnlockAudioDevice(audio_device); }
};

static void audioCallback(void* userdata, Uint8* raw_stream, int raw_length)
{
    SDL_memset(raw_stream, 0, raw_length);

    float* stream = reinterpret_cast<float*>(raw_stream);
    int length = raw_length / sizeof(float);
    while(length > 0)
    {
        //Call the callback at 256Hz, as "events" happen at 256, 128 and 64Hz
        audio.callback(stream, 512);
        stream += 512;
        length -= 512;
    }

    stream = reinterpret_cast<float*>(raw_stream);
    length = raw_length / sizeof(float);
    static float left_high_pass = 0.0f;
    static float right_high_pass = 0.0f;
    for(int n=0; n<length; n+=2)
    {
        float new_value = stream[n] - left_high_pass;
        left_high_pass = (stream[n] - new_value) * 0.997315;
        stream[n] = new_value;

        new_value = stream[n+1] - right_high_pass;
        right_high_pass = (stream[n+1] - new_value) * 0.997315;
        stream[n+1] = new_value;
    }
}

void Audio::init()
{
    if (audio_device)
        return;

    SDL_AudioSpec spec, obtained;

    SDL_zero(spec);
    spec.freq = 65536;
    spec.format = AUDIO_F32;
    spec.channels = 2;
    spec.samples = 2048;
    spec.callback = audioCallback;

    audio_device = SDL_OpenAudioDevice(nullptr, 0, &spec, &obtained, 0);
    SDL_PauseAudioDevice(audio_device, 0);
}

void Audio::callback(float* stream, int length)
{
    if (!(NR52.value & 0x80))
    {
        square_1.active = false;
        square_2.active = false;
        wave.active = false;
        noise.active = false;
        return;
    }
    float left_volume = float((NR50.value >> 4) & 0x07) / float(0x07);
    float right_volume = float(NR50.value & 0x07) / float(0x07);

    uint8_t cm = NR51.value;

    square_1.callback(stream, length, (cm & 0x10) ? left_volume : 0.0, (cm & 0x01) ? right_volume : 0.0);
    square_2.callback(stream, length, (cm & 0x20) ? left_volume : 0.0, (cm & 0x02) ? right_volume : 0.0);
    wave.callback(stream, length, (cm & 0x40) ? left_volume : 0.0, (cm & 0x04) ? right_volume : 0.0);
    noise.callback(stream, length, (cm & 0x80) ? left_volume : 0.0, (cm & 0x08) ? right_volume : 0.0);
}

void Audio::SoundChannel::update()
{
    state = (state + 1) % 4;
    if (!length.update())
        active = false;
    if (state & 1)
    {
        if (!frequency.update())
            active = false;
    }
    if (state == 3)
    {
        if (!volume.update())
            active = false;
    }
}

void Audio::SquareWaveSoundChannel::callback(float* stream, int stream_length, float left_volume, float right_volume)
{
    if (!active)
        return;

    float s = 0.01 * volume.value;
    int freq_div = 2048 - frequency.div;
    for(int n=0; n<stream_length; n+=2)
    {
        //TODO: duty cycle
        stream[n] += (wave_counter > freq_div / 2 ? -s : s) * left_volume;
        stream[n+1] += (wave_counter > freq_div / 2 ? -s : s) * right_volume;
        wave_counter += 2;
        if (wave_counter >= freq_div) wave_counter = 0;
    }

    update();
}

void Audio::WaveSoundChannel::callback(float* stream, int stream_length, float left_volume, float right_volume)
{
    if (!active)
        return;
    if (!(audio.NR30.value & 0x80))
        return;
    int volume_shift = ((audio.NR32.value >> 5) & 0x03) - 1;
    if (volume_shift > -1)
    {
        int freq_div = 2048 - frequency.div;
        for(int n=0; n<stream_length; n+=2)
        {
            int sample = audio.WAVE[wave_counter / 2].value;
            if (wave_counter & 1)
                sample &= 0x0F;
            else
                sample >>= 4;
            stream[n] += 0.01 * (sample >> volume_shift) * left_volume;
            stream[n+1] += 0.01 * (sample >> volume_shift) * right_volume;
            counter += 32;
            if (counter >= freq_div)
            {
                counter -= freq_div;
                wave_counter = (wave_counter + 1) & 0x1F;
            }
        }
    }

    update();
}

void Audio::NoiseSoundChannel::callback(float* stream, int stream_length, float left_volume, float right_volume)
{
    if (!active)
        return;

    float s = 0.01 * volume.value;
    uint8_t conf = audio.NR43.value;
    int freq_div = (conf & 0x07) * 16;
    if (!freq_div) freq_div = 8;
    freq_div <<= (conf >> 4);
    for(int n=0; n<stream_length; n+=2)
    {
        stream[n] += ((lfsr & 0x01) ? -s : s) * left_volume;
        stream[n+1] += ((lfsr & 0x01) ? -s : s) * right_volume;
        wave_counter += 64;
        while(wave_counter >= freq_div)
        {
            wave_counter -= freq_div;
            uint32_t bit = (lfsr ^ (lfsr >> 1)) & 0x01;
            lfsr = (lfsr >> 1) | (bit << 14);
            if (conf & 0x08)
                lfsr = (lfsr & 0x3FBF) | ((lfsr & 0x4000) >> 8);
        }
    }

    update();
}

bool Audio::FrequencySweep::update()
{
    if (sweep_delay && sweep_shift)
    {
        sweep_counter += 1;
        if (sweep_counter >= sweep_delay)
        {
            sweep_counter = 0;
            int diff = div >> sweep_shift;
            if (sweep_sub)
                div -= diff;
            else
                div += diff;
            if (div > 2047)
                return false;
        }
    }
    return true;
}

bool Audio::Length::update()
{
    if (!enabled)
        return true;
    if (counter)
        counter -= 1;
    return counter > 0;
}

bool Audio::VolumeEnvelope::update()
{
    if (sweep_delay)
    {
        sweep_counter += 1;
        if (sweep_counter >= sweep_delay)
        {
            sweep_counter = 0;
            if (sweep_inc && value < 0x0F)
                value += 1;
            if (!sweep_inc && value > 0x00)
                value -= 1;
        }
    }
    return true;
}

uint8_t Audio::NR10Reg::get() const
{
    uint8_t result = (audio.square_1.frequency.sweep_delay << 4) & 0x7F;
    if (audio.square_1.frequency.sweep_sub)
        result |= 0x08;
    result |= audio.square_1.frequency.sweep_shift;
    return result;
}

void Audio::NR10Reg::setImpl(uint8_t value)
{
    LockAudio lock;
    audio.square_1.frequency.sweep_shift = (value & 0x07);
    audio.square_1.frequency.sweep_sub = (value & 0x08);
    audio.square_1.frequency.sweep_delay = (value >> 4) & 0x07;
}

uint8_t Audio::NRx1Reg::get() const
{
    return 0x00; //TODO: duty cycle
}

void Audio::NRx1Reg::setImpl(uint8_t value)
{
    LockAudio lock;
    length.counter = (mask + 1) - (value & mask);
    //TODO: duty cycle
}

uint8_t Audio::NRx2Reg::get() const
{
    uint8_t result = env.value << 4;
    if (env.sweep_inc)
        result |= 0x08;
    result |= (env.sweep_delay) & 0x07;
    return result;
}

void Audio::NRx2Reg::setImpl(uint8_t value)
{
    LockAudio lock;
    env.value = value >> 4;
    env.sweep_inc = value & 0x08;
    env.sweep_delay = value & 0x07;
}

uint8_t Audio::NRx3Reg::get() const
{
    return 0xFF;
}

void Audio::NRx3Reg::setImpl(uint8_t value)
{
    LockAudio lock;
    div = (div & 0xFF00) | value;
}

uint8_t Audio::NRx4Reg::get() const
{
    uint8_t result = 0xBF;
    if (length.enabled)
        result |= 0x40;
    return result;
}

void Audio::NRx4Reg::setImpl(uint8_t value)
{
    LockAudio lock;
    if (value & 0x80)
    {
        active = true;
        if (frequency_div)
            *frequency_div = ((*frequency_div) & 0xFF) | ((value & 0x07) << 8);
    }
    length.enabled = value & 0x40;
}

uint8_t Audio::NR52Reg::get() const
{
    uint8_t result = value;
    if (audio.square_1.active)
        result |= 0x01;
    if (audio.square_2.active)
        result |= 0x02;
    if (audio.wave.active)
        result |= 0x04;
    if (audio.noise.active)
        result |= 0x08;
    return result;
}
