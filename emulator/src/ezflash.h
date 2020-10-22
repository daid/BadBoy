#pragma once

#include "mbc.h"
#include <vector>

class EZFlashMBC : public MBC
{
public:
    EZFlashMBC(const char* image_filename);

    uint32_t mapRom(uint16_t address) override;
    uint32_t mapSRam(uint16_t address) override;
    void writeRom(uint16_t address, uint8_t value) override;
    uint32_t getRomBankNr() override;

private:
    std::vector<uint8_t> image;

    uint32_t rom_bank = 0;
    int unlock = 0;
    int command = 0;

    int image_sector_nr = 0;
    int image_sector_count = 0;
};
