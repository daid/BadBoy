#pragma once

#include "mem8.h"
#include "ram.h"

class Video
{
public:
    class VideoReg : public Mem8
    {
    public:
        uint8_t value;
        uint8_t get() const override { return value; }
        void set(uint8_t value) override { this->value = value; }
    };
    class DmaReg : public Mem8
    {
        uint8_t get() const override;
        void set(uint8_t value) override;
    };
    class PaletteReg : public Mem8
    {
    public:
        uint8_t get() const override;
        void set(uint8_t value) override;

        uint8_t value;
        uint32_t palette[4];
    };
    VideoReg LCDC; //0xFF40
    VideoReg STAT; //0xFF41
    VideoReg SCY; //0xFF42
    VideoReg SCX; //0xFF43
    VideoReg LY;  //0xFF44
    VideoReg LYC; //0xFF45
    DmaReg DMA; //0xFF45
    PaletteReg BGP; //0xFF47
    PaletteReg OBP0; //0xFF48
    PaletteReg OBP1; //0xFF49
    VideoReg WY; //0xFF4A
    VideoReg WX; //0xFF4B
    VideoReg VBK; //0xFF4F

    Mem8Ram vram[0x4000];
    Mem8Ram oam[0xA0];

    uint32_t line_start_cycle;

    void init();
    bool update();

    Mem8& getVRam(uint16_t address);
};

extern Video video;
