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
    virtual bool sramEnabled() { return true; }

private:
    void setSRam(uint32_t bank, uint32_t addr, uint8_t data);

    std::vector<uint8_t> image;

    uint32_t rom_bank = 0;
    uint32_t sram_type = 0;
    uint32_t sram_bank = 0;
    int unlock = 0;
    int command = 0;

    int image_sector_nr = 0;
    int image_sector_count = 0;

    static constexpr uint32_t sram_normal = 0;
    static constexpr uint32_t sram_sd_status = 1;
    static constexpr uint32_t sram_sd_data = 2;
    static constexpr uint32_t sram_rom_status = 3;
    static constexpr uint32_t sram_rtc_data = 4;
    static constexpr uint32_t sram_status = 5;
    static constexpr uint32_t sram_sd_to_rom_data = 6;
};
