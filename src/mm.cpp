#include <stdio.h>
#include "mm.h"
#include "card.h"
#include "ram.h"
#include "dma.h"
#include "cpu.h"
#include "video.h"
#include "audio.h"
#include "input.h"
#include "timer.h"


class Mem8Void : public Mem8
{
    uint8_t get() const override { return 0xff; }
    void setImpl(uint8_t) override {}
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
        return ram.getWRam(address - 0xC000);
    if (address < 0xFE00)
        return ram.getWRam(address - 0xE000); //Mirror
    if (address < 0xFEA0)
        return video.oam[address - 0xFE00];
    if (address < 0xFF00)
        return mem8void;
    if (address < 0xFF80)
    {
        switch(address)
        {
        case 0xFF00: return input;
        //case 0xFF01: return serial.SB;
        //case 0xFF02: return serial.SC;
        case 0xFF04: return timer.DIV;
        case 0xFF05: return timer.TIMA;
        case 0xFF06: return timer.TMA;
        case 0xFF07: return timer.TAC;
        case 0xFF0F: return cpu.IF;
        case 0xFF10: return audio.NR10;
        case 0xFF11: return audio.NR11;
        case 0xFF12: return audio.NR12;
        case 0xFF13: return audio.NR13;
        case 0xFF14: return audio.NR14;
        case 0xFF16: return audio.NR21;
        case 0xFF17: return audio.NR22;
        case 0xFF18: return audio.NR23;
        case 0xFF19: return audio.NR24;
        case 0xFF1A: return audio.NR30;
        case 0xFF1B: return audio.NR31;
        case 0xFF1C: return audio.NR32;
        case 0xFF1D: return audio.NR33;
        case 0xFF1E: return audio.NR34;
        case 0xFF20: return audio.NR41;
        case 0xFF21: return audio.NR42;
        case 0xFF22: return audio.NR43;
        case 0xFF23: return audio.NR44;
        case 0xFF24: return audio.NR50;
        case 0xFF25: return audio.NR51;
        case 0xFF26: return audio.NR52;
        case 0xFF30: return audio.WAVE[0];
        case 0xFF31: return audio.WAVE[1];
        case 0xFF32: return audio.WAVE[2];
        case 0xFF33: return audio.WAVE[3];
        case 0xFF34: return audio.WAVE[4];
        case 0xFF35: return audio.WAVE[5];
        case 0xFF36: return audio.WAVE[6];
        case 0xFF37: return audio.WAVE[7];
        case 0xFF38: return audio.WAVE[8];
        case 0xFF39: return audio.WAVE[9];
        case 0xFF3A: return audio.WAVE[10];
        case 0xFF3B: return audio.WAVE[11];
        case 0xFF3C: return audio.WAVE[12];
        case 0xFF3D: return audio.WAVE[13];
        case 0xFF3E: return audio.WAVE[14];
        case 0xFF3F: return audio.WAVE[15];
        case 0xFF40: return video.LCDC;
        case 0xFF41: return video.STAT;
        case 0xFF42: return video.SCY;
        case 0xFF43: return video.SCX;
        case 0xFF44: return video.LY;
        case 0xFF45: return video.LYC;
        case 0xFF46: return dma.DMA;
        case 0xFF47: return video.BGP;
        case 0xFF48: return video.OBP0;
        case 0xFF49: return video.OBP1;
        case 0xFF4A: return video.WY;
        case 0xFF4B: return video.WX;
        case 0xFF4D: return cpu.KEY1;
        case 0xFF4F: return video.VBK;
        case 0xFF50: return regBootrom;
        case 0xFF51: return dma.HDMA1;
        case 0xFF52: return dma.HDMA2;
        case 0xFF53: return dma.HDMA3;
        case 0xFF54: return dma.HDMA4;
        case 0xFF55: return dma.HDMA5;
        //case 0xFF56: return IR;
        case 0xFF68: return video.BCPS;
        case 0xFF69: return video.BCPD;
        case 0xFF6A: return video.OCPS;
        case 0xFF6B: return video.OCPD;
        case 0xFF70: return ram.SVBK;
        }
        return mem8void;
    }
    if (address < 0xFFFF)
        return ram.getHRam(address - 0xFF80);
    return cpu.IE; //IE
}
