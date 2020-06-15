#include <stdio.h>
#include "mm.h"
#include "card.h"
#include "ram.h"
#include "cpu.h"
#include "video.h"
#include "input.h"
#include "timer.h"


class Mem8Void : public Mem8
{
    uint8_t get() const override { return 0xff; }
    void set(uint8_t) override {}
};
static Mem8Void mem8void;
static Mem8Ram regBootrom;

Mem8& mm::get(uint16_t address)
{
    if (address < 0x0100 && !regBootrom.value)
        return card.getBoot(address);
    if (address < 0x8000)
        return card.getRom(address);
    if (address < 0xA000)
        return video.getVRam(address - 0x8000);
    if (address < 0xC000)
        return card.getSRam(address - 0xA000);
    if (address < 0xE000)
        return wram::get(address - 0xC000);
    if (address < 0xFE00)
        return wram::get(address - 0xE000); //Mirror
    if (address < 0xFEA0)
        return video.oam[address - 0xFE00];
    if (address < 0xFF00)
        return mem8void;
    if (address < 0xFF80)
    {
        switch(address)
        {
        case 0xFF00: return input;
        case 0xFF04: return timer.DIV;
        case 0xFF05: return timer.TIMA;
        case 0xFF06: return timer.TMA;
        case 0xFF07: return timer.TAC;
        case 0xFF0F: return cpu.IF;
        case 0xFF40: return video.LCDC;
        case 0xFF41: return video.STAT;
        case 0xFF42: return video.SCY;
        case 0xFF43: return video.SCX;
        case 0xFF44: return video.LY;
        case 0xFF45: return video.LYC;
        case 0xFF46: return video.DMA;
        case 0xFF47: return video.BGP;
        case 0xFF48: return video.OBP0;
        case 0xFF49: return video.OBP1;
        case 0xFF4A: return video.WY;
        case 0xFF4B: return video.WX;
        case 0xFF4F: return video.VBK;
        case 0xFF50: return regBootrom;
        }
        return mem8void;
    }
    if (address < 0xFFFF)
        return hram::get(address - 0xFF80);
    return cpu.IE; //IE
}
