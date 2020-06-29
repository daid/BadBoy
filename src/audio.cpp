#include "audio.h"
#include <SDL.h>


Audio audio;

static void audioCallback(void*  userdata, Uint8* raw_stream, int raw_length)
{
    SDL_memset(raw_stream, 0, raw_length);

    float* stream = reinterpret_cast<float*>(raw_stream);
    int length = raw_length / sizeof(float);
    while(length > 0)
    {
        //Call the callback at 256Hz, as "events" happen at 256, 128 and 64Hz
        audio.callback(stream, 256);
        stream += 256;
        length -= 256;
    }

    stream = reinterpret_cast<float*>(raw_stream);
    length = raw_length / sizeof(float);
    static float high_pass = 0.0f;
    for(int n=0; n<length; n++)
    {
        float new_value = stream[n] - high_pass;
        high_pass = (stream[n] - new_value) * 0.997315;
        stream[n] = new_value;
    }
}

void Audio::init()
{
    SDL_AudioSpec spec, obtained;

    SDL_zero(spec);
    spec.freq = 65536;
    spec.format = AUDIO_F32;
    spec.channels = 1;
    spec.samples = 2048;
    spec.callback = audioCallback;

    SDL_AudioDeviceID dev = SDL_OpenAudioDevice(nullptr, 0, &spec, &obtained, 0);
    SDL_PauseAudioDevice(dev, 0);
}

void Audio::callback(float* stream, int length)
{
    if (!(NR52.value & 0x80))
    {
        square_1.active = false;
        square_2.active = false;
        return;
    }

    if (NR14.value & 0x80)
    {
        square_1.active = true;
        square_1.freq_div = (2048 - ((int(NR14.value & 0x07) << 8) | NR13.value)) / 2;
        square_1.length = 0;
        if (NR14.value & 0x40)
            square_1.length = 64 - (NR11.value & 0x3F);
        square_1.duty = (NR11.value >> 6);
        square_1.freq_sweep_shift = (NR10.value & 0x07);
        square_1.freq_sweep_sub = (NR10.value & 0x08);
        square_1.freq_sweep_delay = (NR10.value >> 4) & 0x07;
        square_1.volume = (NR12.value >> 4);
        square_1.volume_sweep_inc = (NR12.value & 0x08);
        square_1.volume_sweep_delay = (NR12.value & 0x07);
        NR14.value = 0;
    }
    if (NR24.value & 0x80)
    {
        square_2.active = true;
        square_2.freq_div = (2048 - ((int(NR24.value & 0x07) << 8) | NR23.value)) / 2;
        square_2.length = 0;
        if (NR24.value & 0x40)
            square_2.length = 64 - (NR21.value & 0x3F);
        square_2.duty = (NR21.value >> 6);
        square_2.volume = (NR22.value >> 4);
        square_2.volume_sweep_inc = (NR22.value & 0x08);
        square_2.volume_sweep_delay = (NR22.value & 0x07);
        NR24.value = 0;
    }
    if (NR34.value & 0x80)
    {
        wave.active = true;
        wave.freq_div = (2048 - ((int(NR34.value & 0x07) << 8) | NR33.value));
        if (NR34.value & 0x40)
            wave.length = 256 - NR31.value;
        NR34.value = 0;
    }
    if (NR44.value & 0x80)
    {
        noise.active = true;
        noise.freq_div = (2048 - ((int(NR44.value & 0x07) << 8) | NR43.value)) / 2;
        noise.length = 0;
        if (NR44.value & 0x40)
            noise.length = 64 - (NR41.value & 0x3F);
        noise.volume = (NR42.value >> 4);
        noise.volume_sweep_inc = (NR42.value & 0x08);
        noise.volume_sweep_delay = (NR42.value & 0x07);
        NR44.value = 0;
    }
    square_1.callback(stream, length);
    square_2.callback(stream, length);
    wave.callback(stream, length);
    noise.callback(stream, length);
}

void Audio::SoundChannel::callback(float* stream, int stream_length)
{
    if (!active)
        return;

    float s = 0.01 * volume;
    for(int n=0; n<stream_length; n++)
    {
        //TODO: duty cycle
        stream[n] += wave_counter > freq_div / 2 ? -s : s;
        wave_counter += 1;
        if (wave_counter >= freq_div) wave_counter = 0;
    }

    state = (state + 1) % 4;
    if (length)
    {
        length -= 1;
        if (!length)
            active = false;
    }
    if ((state & 1) && freq_sweep_delay)
    {
        freq_sweep_counter += 1;
        if (freq_sweep_counter >= freq_sweep_delay)
        {
            freq_sweep_counter = 0;
            int diff = freq_div >> freq_sweep_shift;
            if (freq_sweep_sub)
                freq_div -= diff;
            else
                freq_div += diff;
        }
    }
    if (state == 3 && volume_sweep_delay)
    {
        volume_sweep_counter += 1;
        if (volume_sweep_counter >= volume_sweep_delay)
        {
            volume_sweep_counter = 0;
            if (volume_sweep_inc && volume < 0x0F)
                volume += 1;
            if (!volume_sweep_inc && volume > 0x00)
                volume -= 1;
        }
    }
}
