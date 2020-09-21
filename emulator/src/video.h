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
        void setImpl(uint8_t value) override { this->value = value; }
    };
    class PaletteReg : public Mem8
    {
    public:
        uint8_t get() const override;
        void setImpl(uint8_t value) override;

        uint8_t value;
        uint32_t palette[4];
    };
    class ColorPaletteReg : public Mem8
    {
    public:
        ColorPaletteReg(VideoReg& index) : index(index) {}

        uint8_t get() const override;
        void setImpl(uint8_t value) override;

        uint8_t data[0x40];
        uint32_t palette[0x20];

        VideoReg& index;
    };
    VideoReg LCDC; //0xFF40
    VideoReg STAT; //0xFF41
    VideoReg SCY; //0xFF42
    VideoReg SCX; //0xFF43
    VideoReg LY;  //0xFF44
    VideoReg LYC; //0xFF45
    PaletteReg BGP; //0xFF47
    PaletteReg OBP0; //0xFF48
    PaletteReg OBP1; //0xFF49
    VideoReg WY; //0xFF4A
    VideoReg WX; //0xFF4B
    VideoReg VBK; //0xFF4F
    VideoReg BCPS;//0xFF68
    ColorPaletteReg BCPD{BCPS}; //0xFF69
    VideoReg OCPS;//0xFF6A
    ColorPaletteReg OCPD{OCPS}; //0xFF6B

    Mem8Block<Mem8Ram> vram;
    Mem8Block<Mem8Ram> oam;

    uint32_t line_start_cycle;
    int frame_skip_counter = 0;

    void init();
    bool update();
    void dumpInstrumentation(FILE* f);

    Mem8& getVRam(uint16_t address);
};

extern Video video;
