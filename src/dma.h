#pragma once

#include "ram.h"


class DMA
{
public:
    class DmaReg : public Mem8
    {
        uint8_t get() const override;
        void setImpl(uint8_t value) override;
    };
    class HdmaReg : public Mem8
    {
        uint8_t get() const override;
        void setImpl(uint8_t value) override;
    };

    DmaReg DMA; //0xFF45
    Mem8Ram HDMA1;
    Mem8Ram HDMA2;
    Mem8Ram HDMA3;
    Mem8Ram HDMA4;
    HdmaReg HDMA5;
};
extern DMA dma;