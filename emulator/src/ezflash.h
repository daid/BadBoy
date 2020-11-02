#pragma once

#include "mbc.h"
#include "mem8.h"
#include <vector>

class EZFlashMBC : public MBC
{
public:
    EZFlashMBC(const char* image_filename);

    uint32_t mapRom(uint16_t address) override;
    uint32_t mapSRam(uint16_t address) override;
    void writeRom(uint16_t address, uint8_t value) override;
    uint32_t getRomBankNr() override;
    bool sramEnabled() override;

    enum class SRamTarget {
        None,
        SDStatus,
        SDData,
        RomLoadStatus,
        RTC,
        SRAM,
        RomLoadInfo,
        FWVersion,
        FirmwareUpdateStatus,
        Unknown,
        MAX
    };
private:

    Mem8& getSRam(uint32_t addr) { return getSRam(sram_target, addr); }
    Mem8& getSRam(SRamTarget target, uint32_t addr);
    void loadNewRom();

    std::vector<uint8_t> sd_image;

    uint32_t rom_bank = 0;
    SRamTarget sram_target = SRamTarget::None;
    uint32_t sram_bank = 0;
    int unlock = 0;

    int image_sector_nr = 0;
    int image_sector_count = 0;
    int target_mbc = 0;
};
