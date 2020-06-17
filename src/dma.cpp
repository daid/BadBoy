#include "dma.h"
#include "video.h"
#include "mm.h"

DMA dma;


uint8_t DMA::DmaReg::get() const
{
    return 0x00;
}

void DMA::DmaReg::setImpl(uint8_t value)
{
    uint16_t addr = value << 8;
    for(int n=0; n<0xA0; n++)
    {
        video.oam[n].set(mm::get(addr++));
    }
}

uint8_t DMA::HdmaReg::get() const
{
    return 0x80;
}

void DMA::HdmaReg::setImpl(uint8_t value)
{
    uint16_t size = (value & 0x7F) * 0x10 + 0x10;
    uint16_t src = (dma.HDMA2.get() & 0xF0) | (dma.HDMA1.get() << 8);
    uint16_t dst = (dma.HDMA4.get() & 0xF0) | (dma.HDMA2.get() << 8);
    dst = (dst & 0x1FF0) | 0x8000;
    while(size)
    {
        mm::get(dst++).set(mm::get(src++));
        size--;
    }
}
