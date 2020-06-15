#include <SDL.h>
#include "input.h"

Input input;


uint8_t Input::get() const
{
    switch(mode)
    {
    case Mode::None: return 0x00;
    case Mode::Buttons: return buttons ^ 0x3F;
    case Mode::Directions: return directions ^ 0x3F;
    }
    return 0x00;
}

void Input::set(uint8_t value)
{
    if (!(value & 0x20))
        mode = Mode::Buttons;
    else if (!(value & 0x10))
        mode = Mode::Directions;
    else
        mode = Mode::None;
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
            break;
        }
    }
}
