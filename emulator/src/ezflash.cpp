#include "ezflash.h"
#include "card.h"
#include "cpu.h"
#include "input.h"

#include <stdio.h>
#include <assert.h>
#include <time.h>

static int dec2bcd(int n)
{
    return (n % 10) | (n / 10 * 16);
}

std::array<uint32_t, int(EZFlashMBC::SRamTarget::MAX)> SRAM_OFFSET;
std::array<uint32_t, int(EZFlashMBC::SRamTarget::MAX)> SRAM_SIZE{ // Make sure this array matches the enum!
    0x0000, //None,
    0x0001, //SDStatus,
    0x0800, //SDData,
    0x0001, //RomLoadStatus,
    0x0100, //RTC,
    0x40 * 0x2000, //SRAM,
    0x2000, //RomLoadInfo: TODO check size of this,
    0x0001, //FWVersion,
    0x2000, //Unknown
};


EZFlashMBC::EZFlashMBC(const char* image_filename)
{
    FILE* f = fopen(image_filename, "rb");
    fseek(f, 0, SEEK_END);
    sd_image.resize(ftell(f));
    fseek(f, 0, SEEK_SET);
    if (fread(sd_image.data(), 1, sd_image.size(), f) != sd_image.size())
        printf("Failed to read sd card image...\n");
    fclose(f);

    // We resize the rom to the biggest size, to pre-allocate enough memory
    // This is done else the instrumentation crashes due to pointer usage.
    card.resizeRom(256 * 0x4000);

    //Initialize the SRAM_OFFSET array and resize the amount of SRAM we have to account for everything we need to
    // map to SRAM.
    uint32_t offset = 0;
    for(size_t n=0; n<SRAM_SIZE.size(); n++)
    {
        SRAM_OFFSET[n] = offset;
        offset += SRAM_SIZE[n];
    }
    card.resizeSRam(offset);

    //Setting this indicates that the battery is not dry.
    // Loader sets this to 0x88 quite often when it is running.
    getSRam(SRamTarget::SRAM, 0x11 * 0x2000 + 0x201).set(0x88);
}

uint32_t EZFlashMBC::mapRom(uint16_t address)
{
    if (address < 0x4000)
        return address;
    return (address & 0x3fff) | rom_bank * 0x4000;
}

uint32_t EZFlashMBC::mapSRam(uint16_t address)
{
    if (sram_target == SRamTarget::SRAM)
        address += sram_bank * 0x2000;
    if (sram_target == SRamTarget::Unknown) printf("  SRAM access: %02x:%04x\n", int(sram_target), address);
    return SRAM_OFFSET[int(sram_target)] + (address % SRAM_SIZE[int(sram_target)]);
}

void EZFlashMBC::writeRom(uint16_t address, uint8_t value)
{
    if (address == 0x2000)
    {
        //The EZFlash seems to write 0xFF to the bank number but then never accesses the top bank.
        // But it seems to default to bank 0x01 when tested on real hardware.
        if (value == 0xff)
            value = 0x01;
        rom_bank = value;
    } else if (address == 0x4000) {
        sram_bank = value & 0x3F;
        printf("SRAM Bank: %02x\n", sram_bank);
    } else if (address == 0x7f00) {
        if (value == 0xE1 && unlock == 0) unlock = 1; else unlock = 0;
    } else if (address == 0x7f10) {
        if (value == 0xE2 && unlock == 1) unlock = 2; else unlock = 0;
    } else if (address == 0x7f20) {
        if (value == 0xE3 && unlock == 2) unlock = 3; else unlock = 0;
    } else if (address == 0x7f30 && unlock == 3) {
        //"SD" commands?
        //printf("Switch SRAM MUX1: %02x EZFlash ROM Write: %04x:%02x from %02x:%04x\n", value, address, value, cpu.pc >= 0x4000 ? rom_bank : 0, cpu.pc);
        switch(value)
        {
        case 0: //Normal SRAM?
            sram_target = SRamTarget::None;
            break;
        case 1: //SD card sector data
            sram_target = SRamTarget::SDData;
            break;
        case 3: // SD card command state
            sram_target = SRamTarget::SDStatus;
            break;
        default:
            printf("Unknown value written to MUX1: %02x EZFlash ROM Write: %04x:%02x from %02x:%04x\n", value, address, value, cpu.pc >= 0x4000 ? rom_bank : 0, cpu.pc);
            break;
        }
    } else if (address == 0x7f36 && unlock == 3) {
        //"ROM" commands?
        printf("Switch SRAM MUX2: %02x EZFlash ROM Write: %04x:%02x from %02x:%04x\n", value, address, value, cpu.pc >= 0x4000 ? rom_bank : 0, cpu.pc);
        switch(value)
        {
        case 0: //Normal SRAM?
            sram_target = SRamTarget::None;
            break;
        case 1:
            sram_target = SRamTarget::RomLoadInfo;
            break;
        case 3: // command state of ROM update?
            if (sram_target == SRamTarget::RomLoadInfo)
            {
                loadNewRom();
            }
            sram_target = SRamTarget::RomLoadStatus;
            getSRam(SRamTarget::RomLoadStatus, 0).set(0x02);
            break;
        default:
            printf("Unknown value written to MUX2: %02x EZFlash ROM Write: %04x:%02x from %02x:%04x\n", value, address, value, cpu.pc >= 0x4000 ? rom_bank : 0, cpu.pc);
            break;
        }
    } else if (address == 0x7fc0 && unlock == 3) {
        printf("Switch SRAM MUX3: %02x EZFlash ROM Write: %04x:%02x from %02x:%04x\n", value, address, value, cpu.pc >= 0x4000 ? rom_bank : 0, cpu.pc);
        switch(value)
        {
        case 0: //Switches back to normal SRAM?
            //if (sram_type == sram_status) printf("STATUS 0x201: %02x\n", card.getSRam(0x201).get());
            sram_target = SRamTarget::None;
            break;
        case 2:
            //Used by the initial boot stage, reason is unknown...
            break;
        case 3:
            sram_target = SRamTarget::SRAM;
            break;
        case 4:
            sram_target = SRamTarget::FWVersion;
            getSRam(0).set(10);
            break;
        case 6:
            // This switches to RTC registers, writting to them is ignored by this implementation.
            // Unknown if these are latched or not, but current loader switches this on all the time before reading.
            {
                time_t rawtime;
                time (&rawtime);
                tm* timeinfo = localtime(&rawtime);

                sram_target = SRamTarget::RTC;
                getSRam(8).set(dec2bcd(timeinfo->tm_sec));
                getSRam(9).set(dec2bcd(timeinfo->tm_min));
                getSRam(10).set(dec2bcd(timeinfo->tm_hour));
                getSRam(11).set(dec2bcd(timeinfo->tm_mday));
                getSRam(12).set(dec2bcd(timeinfo->tm_wday));
                getSRam(13).set(dec2bcd(timeinfo->tm_mon + 1));
                getSRam(14).set(dec2bcd(timeinfo->tm_year % 100));
            }
            break;
        default:
            printf("Unknown value written to MUX3: %02x EZFlash ROM Write: %04x:%02x from %02x:%04x\n", value, address, value, cpu.pc >= 0x4000 ? rom_bank : 0, cpu.pc);
            break;
        }
    } else if (address == 0x7fd0 && unlock == 3) {
        printf("RTC update\n");
    } else if (address == 0x7fb0 && unlock == 3) {
        image_sector_nr = (image_sector_nr & 0xFFFFFF00) | value;
    } else if (address == 0x7fb1 && unlock == 3) {
        image_sector_nr = (image_sector_nr & 0xFFFF00FF) | (value << 8);
    } else if (address == 0x7fb2 && unlock == 3) {
        image_sector_nr = (image_sector_nr & 0xFF00FFFF) | (value << 16);
    } else if (address == 0x7fb3 && unlock == 3) {
        image_sector_nr = (image_sector_nr & 0x00FFFFFF) | (value << 24);
    } else if (address == 0x7fb4 && unlock == 3) {
        image_sector_count = value; // unsure, only seen value 1 so far.
        printf("Accessing SD Sector: %08x:%02x\n", image_sector_nr, image_sector_count);
        if (value & 0x80)
        {
            for(int n=0; n<0x200 * (value & 0x03); n++)
                sd_image[image_sector_nr * 0x200 + n] = getSRam(SRamTarget::SDData, n).get();
        }else{
            for(int n=0; n<0x200 * (value & 0x03); n++)
                getSRam(SRamTarget::SDData, n).set(sd_image[image_sector_nr * 0x200 + n]);
        }
        getSRam(SRamTarget::SDStatus, 0).set(1);
    } else if (address == 0x7f37 && unlock == 3) {
        printf("Preparing target MBC to: %02x\n", value);
    } else if (address == 0x7fc1 && unlock == 3) {
        printf("Preparing ROM mask (low) to: %02x\n", value);
    } else if (address == 0x7fc2 && unlock == 3) {
        printf("Preparing ROM mask (high) to: %02x\n", value);
    } else if (address == 0x7fc3 && unlock == 3) {
        printf("Preparing header checksum?!?: %02x\n", value);
    } else if (address == 0x7fc4 && unlock == 3) {
        printf("Preparing SRAM mask to: %02x\n", value);
    //} else if (address == 0x7fd4 && unlock == 3) { 
    //It seems to write $00 to this before preparing the cart for reboot, reason is unknown
    } else if (address == 0x7fe0 && unlock == 3) {
        if (value == 0x80)
        {
            //Start loaded rom (should reset and apply above prepared settings)
            input.quit = true;
        }
    } else if (address == 0x7ff0) {
        if (value == 0xE4 && unlock == 3) {
            //printf("LOCK/EXEC?\n");
        }
        unlock = 0;
    } else {
        printf("Unknown EZFlash ROM Write: %04x:%02x from %02x:%04x\n", address, value, cpu.pc >= 0x4000 ? rom_bank : 0, cpu.pc);
    }
}

uint32_t EZFlashMBC::getRomBankNr()
{
    return rom_bank;
}

Mem8& EZFlashMBC::getSRam(SRamTarget target, uint32_t addr)
{
    addr = SRAM_OFFSET[int(target)] + (addr % SRAM_SIZE[int(target)]);
    return card.getRawSRam(addr);
}

void EZFlashMBC::loadNewRom()
{
    //Load the buffer into 128 32bit integers so we can use those.
    uint32_t buffer[128];

    for(int n=0; n<128; n++)
    {
        buffer[n] = 
            getSRam(SRamTarget::RomLoadInfo, n * 4 + 0).get() << 0 |
            getSRam(SRamTarget::RomLoadInfo, n * 4 + 1).get() << 8 |
            getSRam(SRamTarget::RomLoadInfo, n * 4 + 2).get() << 16 |
            getSRam(SRamTarget::RomLoadInfo, n * 4 + 3).get() << 24;

        if (n % 4 == 0) printf("%02x:", n);
        printf(" %08x", buffer[n]);
        if (n % 4 == 3) printf("\n");
    }
    
    uint32_t rom_size = buffer[124];
    printf("Loading new rom, size: %d\n", rom_size);
    if (!rom_size)
    {
        printf("Loading empty rom, abort!\n");
        input.quit = true;
        return;
    }

    uint32_t addr = 0;
    card.resizeRom(rom_size);
    int index = 1;
    while(1)
    {
        if (addr >= rom_size)
            break;
        uint32_t sector = buffer[index++];
        uint32_t count = buffer[index++];
        //printf("%08x %08x\n", sector, count);
        while(count)
        {
            if (addr >= rom_size)
                break;
            for(int n=0; n<512; n++)
                card.updateRom(addr+n, sd_image[sector * 512 + n]);
            addr += 512;
            sector++;
            count--;
        }
    }
}
