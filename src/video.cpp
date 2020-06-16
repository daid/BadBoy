#include <SDL.h>
#include <stdio.h>
#include <algorithm>
#include "video.h"
#include "cpu.h"
#include "mm.h"

Video video;

SDL_Window* window;
SDL_Surface* window_surface;
SDL_Surface* backbuffer;

void Video::init()
{
    SDL_Init(SDL_INIT_EVERYTHING);
    window = SDL_CreateWindow("BadBoy", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 160 * 4, 144 * 4, SDL_WINDOW_SHOWN);
    window_surface = SDL_GetWindowSurface(window);
    backbuffer = SDL_CreateRGBSurface(0, 160, 144, 32, 0, 0, 0, 0);

    for(uint32_t n=0; n<0x4000; n++)
        vram[n].id = n | ID_VRAM;
    for(uint32_t n=0; n<0xA0; n++)
        oam[n].id = n | ID_OAM;
}

bool Video::update()
{
    if (cpu.cycles < line_start_cycle + 456)
        return false;
    line_start_cycle += 456;
    uint8_t line = LY.get();
    LY.set((line + 1) % 154);
    if (LY.value == LYC.value)
    {
        STAT.value |= 0x04;
        if (STAT.value & 0x80)
            cpu.setInterrupt(0x02);
    }
    else
    {
        STAT.value &=~0x04;
    }
    if (line < 144)
    {
        SDL_LockSurface(backbuffer);
        uint32_t* line_ptr = static_cast<uint32_t*>(backbuffer->pixels);
        line_ptr += line * backbuffer->pitch / sizeof(uint32_t);
        int background_tile_index = 0x1800 + (((line + SCY.get()) / 8) % 0x20) * 0x20;
        if (LCDC.value & 0x08)
            background_tile_index += 0x0400;
        int background_tile_y = (line + SCY.get()) % 8;
        for(int x=0; x<160; x++)
        {
            int bgx = (x + SCX.get()) & 0xFF;
            uint8_t background_tile = vram[background_tile_index + bgx / 8].get();
            uint8_t background_attr = vram[background_tile_index + bgx / 8 + 0x2000].get();
            int tile_data_index = 0x0000 + background_tile * 16;
            if (background_attr & 0x40)
                tile_data_index += 14 - (background_tile_y * 2);
            else
                tile_data_index += background_tile_y * 2;
            if (!(LCDC.value & 0x10) && tile_data_index < 0x0800)
                tile_data_index |= 0x1000;
            if (background_attr & 0x08)
                tile_data_index |= 0x2000;
            uint8_t a = vram[tile_data_index + 0].get();
            uint8_t b = vram[tile_data_index + 1].get();
            int pal_idx = 0;
            uint8_t bit;
            if (background_attr & 0x20)
                bit = 0x01 << (bgx & 7);
            else
                bit = 0x80 >> (bgx & 7);
            if (a & bit)
                pal_idx |= 1;
            if (b & bit)
                pal_idx |= 2;
            if (cpu.gbc)
                line_ptr[x] = BCPD.palette[(background_attr & 0x07) * 4 + pal_idx];
            else
                line_ptr[x] = BGP.palette[pal_idx];
        }
        if (video.LCDC.value & 0x20 && line >= WY.value)
        {
            int window_tile_index = 0x1800 + (((line - WY.value) / 8) % 0x20) * 0x20;
            if (LCDC.value & 0x40)
                window_tile_index += 0x0400;
            int window_tile_y = (line - WY.value) % 8;
            for(int x=std::max(0, WX.value-7); x<160; x++)
            {
                int wx = x - (WX.value-7);
                uint8_t window_tile = vram[window_tile_index + wx / 8].get();
                uint8_t window_attr = vram[(window_tile_index + wx / 8) | 0x2000].get();
                int tile_data_index = 0x0000 + window_tile * 16;
                if (window_attr & 0x40)
                    tile_data_index += 14 - (window_tile_y * 2);
                else
                    tile_data_index += window_tile_y * 2;
                if (!(LCDC.value & 0x10) && tile_data_index < 0x0800)
                    tile_data_index |= 0x1000;
                if (window_attr & 0x08)
                    tile_data_index |= 0x2000;
                uint8_t a = vram[tile_data_index + 0].get();
                uint8_t b = vram[tile_data_index + 1].get();
                int pal_idx = 0;
                uint8_t bit;
                if (window_attr & 0x20)
                    bit = 0x01 << (wx & 7);
                else
                    bit = 0x80 >> (wx & 7);
                if (a & bit)
                    pal_idx |= 1;
                if (b & bit)
                    pal_idx |= 2;
                if (cpu.gbc)
                    line_ptr[x] = BCPD.palette[(window_attr & 0x07) * 4 + pal_idx];
                else
                    line_ptr[x] = BGP.palette[pal_idx];
            }
        }
        if (video.LCDC.value & 0x02)
        {
            int sprite_size = 8;
            if (video.LCDC.value & 0x04)
                sprite_size = 16;
            for(int idx=0xA0-4; idx>=0x00; idx-=4)
            {
                int y = int(oam[idx].value) - line - 16 + sprite_size - 1;
                if (y < 0 || y >= sprite_size)
                    continue;
                int x = int(oam[idx+1].value) - 8;
                int tile_index = int(oam[idx+2].value) * 16;
                if (oam[idx+3].value & 0x40)
                    tile_index += y * 2;
                else
                    tile_index += (sprite_size - 1 - y) * 2;
                uint8_t a = vram[tile_index + 0].get();
                uint8_t b = vram[tile_index + 1].get();
                uint32_t* pal = OBP0.palette;
                if (oam[idx+3].value & 0x10)
                    pal = OBP1.palette;
                if (cpu.gbc)
                    pal = OCPD.palette + 4 * (oam[idx+3].value & 0x07);
                for(int bit=0; bit<8; bit++)
                {
                    if (x+bit < 0 || x+bit >= 160)
                        continue;
                    int pal_idx = 0;
                    uint8_t mask;
                    if (oam[idx+3].value & 0x20)
                        mask = 0x01 << bit;
                    else
                        mask = 0x80 >> bit;
                    if (a & mask)
                        pal_idx |= 1;
                    if (b & mask)
                        pal_idx |= 2;
                    if (pal_idx != 0)
                    {
                        line_ptr[x+bit] = pal[pal_idx];
                    }
                }
            }
        }
        SDL_UnlockSurface(backbuffer);
    }

    if (line == 144)
    {
        if (LCDC.value & 0x80)
            cpu.setInterrupt(0x01);
    }

    if (line < 153)
        return false;

    SDL_BlitScaled(backbuffer, nullptr, window_surface, nullptr);
    SDL_UpdateWindowSurface(window);
    SDL_Delay(1);
    return true;
}

Mem8& Video::getVRam(uint16_t address)
{
    if (VBK.value & 0x01 && cpu.gbc)
        return vram[address | 0x2000];
    return vram[address];
}

uint8_t Video::DmaReg::get() const
{
    return 0x00;
}

void Video::DmaReg::setImpl(uint8_t value)
{
    uint16_t addr = value << 8;
    for(int n=0; n<0xA0; n++)
    {
        video.oam[n].set(mm::get(addr++).get());
    }
}

uint8_t Video::PaletteReg::get() const
{
    return value;
}

void Video::PaletteReg::setImpl(uint8_t value)
{
    this->value = value;
    for(int n=0; n<4; n++)
    {
        switch((value >> (n * 2)) & 0x03)
        {
        case 0: palette[n] = 0xFFFFFF; break;
        case 1: palette[n] = 0xAAAAAA; break;
        case 2: palette[n] = 0x555555; break;
        case 3: palette[n] = 0x000000; break;
        }
    }
}

uint8_t Video::ColorPaletteReg::get() const
{
    return data[index.get() & 0x3F];
}

void Video::ColorPaletteReg::setImpl(uint8_t value)
{
    int idx = index.get() & 0x3F;
    data[idx] = value;
    if (index.get() & 0x80)
        index.set(((idx + 1) & 0x3F) | 0x80);

    uint16_t color16 = data[idx & 0x3E] | (data[idx | 0x01] << 8);
    palette[idx / 2] =
        (((color16 >> 0) & 0x1F) << 19) |
        (((color16 >> 5) & 0x1F) << 11) |
        (((color16 >> 10) & 0x1F) << 3);
}
