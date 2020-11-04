#include <SDL.h>
#include "input.h"

Input input;


uint8_t Input::get() const
{
    uint8_t result = mode;
    if (!(result & 0x20))
        result &=~buttons;
    if (!(result & 0x10))
        result &=~directions;
    return result;
}

void Input::setImpl(uint8_t value)
{
    mode = value | 0xCF;
}

void Input::setReplayFile(const char* filename, bool playback)
{
    if (playback)
        replay_file = fopen(filename, "rb");
    else
        replay_file = fopen(filename, "wb");
    replay_playback = playback;
}

void Input::update()
{
    SDL_Event e;
    while(SDL_PollEvent(&e))
    {
        switch(e.type)
        {
        case SDL_QUIT: quit = true; break;
        case SDL_KEYDOWN:
            if (e.key.keysym.sym == SDLK_DOWN) directions |= 0x08;
            if (e.key.keysym.sym == SDLK_UP) directions |= 0x04;
            if (e.key.keysym.sym == SDLK_LEFT) directions |= 0x02;
            if (e.key.keysym.sym == SDLK_RIGHT) directions |= 0x01;

            if (e.key.keysym.sym == SDLK_RETURN) buttons |= 0x08;
            if (e.key.keysym.sym == SDLK_RSHIFT) buttons |= 0x04;
            if (e.key.keysym.sym == SDLK_a) buttons |= 0x02;
            if (e.key.keysym.sym == SDLK_s) buttons |= 0x01;

            if (e.key.keysym.sym == SDLK_TAB) fast_forward = 1;
            if (e.key.keysym.sym == SDLK_BACKSPACE) fast_forward = 100;

            if (e.key.keysym.sym == SDLK_ESCAPE) quit = true;
            break;
        case SDL_KEYUP:
            if (e.key.keysym.sym == SDLK_DOWN) directions &=~0x08;
            if (e.key.keysym.sym == SDLK_UP) directions &=~0x04;
            if (e.key.keysym.sym == SDLK_LEFT) directions &=~0x02;
            if (e.key.keysym.sym == SDLK_RIGHT) directions &=~0x01;

            if (e.key.keysym.sym == SDLK_RETURN) buttons &=~0x08;
            if (e.key.keysym.sym == SDLK_RSHIFT) buttons &=~0x04;
            if (e.key.keysym.sym == SDLK_a) buttons &=~0x02;
            if (e.key.keysym.sym == SDLK_s) buttons &=~0x01;

            if (e.key.keysym.sym == SDLK_TAB) fast_forward = 0;
            if (e.key.keysym.sym == SDLK_BACKSPACE) fast_forward = 0;
            break;
        }
    }
    if (replay_file)
    {
        uint8_t data = (directions << 4) | (buttons & 0x0F);
        if (replay_playback)
        {
            if (fread(&data, 1, 1, replay_file) < 1)
            {
                fclose(replay_file);
                fprintf(stderr, "Replay playback done.\n");
                replay_file = nullptr;
                fast_forward = 0;
            }
            directions = data >> 4;
            buttons = data & 0x0F;
        }
        else
        {
            fwrite(&data, 1, 1, replay_file);
        }
    }
}
