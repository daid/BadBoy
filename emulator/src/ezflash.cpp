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


EZFlashMBC::EZFlashMBC(const char* image_filename)
{
    FILE* f = fopen(image_filename, "rb");
    fseek(f, 0, SEEK_END);
    image.resize(ftell(f));
    fseek(f, 0, SEEK_SET);
    if (fread(image.data(), 1, image.size(), f) != image.size())
        printf("Failed to read sd card image...\n");
    fclose(f);

    // Force to have a lot of SRAM data so we can manage our data somewhat.
    card.resizeSRam(0x2000 * 256 * 16);
}

uint32_t EZFlashMBC::mapRom(uint16_t address)
{
    if (address < 0x4000)
        return address;
    return (address & 0x3fff) | rom_bank * 0x4000;
}

uint32_t EZFlashMBC::mapSRam(uint16_t address)
{
    if (sram_type == sram_rtc_data)
        return address + sram_type * 0x2000 * 256;
    //if (sram_type != sram_sd_data) printf("  SRAM access: %02x:%04x\n", sram_type, sram_bank, address);
    if (sram_type == sram_unknown) printf("  SRAM access: %02x:%02x:%04x\n", sram_type, sram_bank, address);
    return address + sram_bank * 0x2000 + sram_type * 0x2000 * 256;
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
        sram_bank = value;
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
            sram_type = sram_normal;
            break;
        case 1: //SD card sector data
            sram_type = sram_sd_data;
            for(int n=0; n<512; n++)
                setSRam(0, n, image[n + image_sector_nr * 512]);
            break;
        case 3: // SD card command state?
            sram_type = sram_sd_status;
            setSRam(0, 0, 0x01);
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
            sram_type = sram_normal;
            break;
        case 1:
            sram_type = sram_sd_to_rom_data;
            break;
        case 3: // command state of ROM update?
            if (sram_type == sram_sd_to_rom_data)
            {
                loadNewRom();
            }
            sram_type = sram_rom_status;
            setSRam(0, 0, 0x02);
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
            sram_type = sram_normal;
            break;
        case 2:
            //Used by the initial boot stage, reason is unknown...
            break;
        case 3:
            sram_type = sram_status;
            //Setting this indicates that there is SRAM to be backed up to SD card, exact workings unknown.
            //setSRam(0x11, 0x000, 0xAA);

            //Setting this indicates that the battery is not dry. (we should only do this on init)
            // Loader sets this to 0x88 quite often when it is running.
            setSRam(0x11, 0x201, 0x88);
            break;
        case 4:
            sram_type = sram_fw_version;
            setSRam(0x00, 0x000, 10);
            break;
        case 6:
            // This switches to RTC registers, writting to them is ignored by this implementation.
            // Unknown if these are latched or not, but current loader switches this on all the time before reading.
            {
                time_t rawtime;
                time (&rawtime);
                tm* timeinfo = localtime(&rawtime);

                sram_type = sram_rtc_data;
                setSRam(0x00, 8, dec2bcd(timeinfo->tm_sec));
                setSRam(0x00, 9, dec2bcd(timeinfo->tm_min));
                setSRam(0x00, 10, dec2bcd(timeinfo->tm_hour));
                setSRam(0x00, 11, dec2bcd(timeinfo->tm_mday));
                //setSRam(0x00, 12).set(dec2bcd(timeinfo->)); ?? unknown maybe week day, need to test on hardware
                setSRam(0x00, 13, dec2bcd(timeinfo->tm_mon + 1));
                setSRam(0x00, 14, dec2bcd(timeinfo->tm_year % 100));
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

void EZFlashMBC::setSRam(uint32_t bank, uint32_t address, uint8_t data)
{
    card.getRawSRam(address + bank * 0x2000 + sram_type * 0x2000 * 256).set(data);
}

void EZFlashMBC::loadNewRom()
{
    //Load the buffer into 128 32bit integers so we can use those.
    uint32_t buffer[128];

    for(int n=0; n<128; n++)
    {
        buffer[n] = 
            card.getRawSRam(n * 4 + 0 + sram_sd_to_rom_data * 0x2000 * 256).get() << 0 |
            card.getRawSRam(n * 4 + 1 + sram_sd_to_rom_data * 0x2000 * 256).get() << 8 |
            card.getRawSRam(n * 4 + 2 + sram_sd_to_rom_data * 0x2000 * 256).get() << 16 |
            card.getRawSRam(n * 4 + 3 + sram_sd_to_rom_data * 0x2000 * 256).get() << 24;

        if (n % 4 == 0) printf("%02x:", n);
        printf(" %08x", buffer[n]);
        if (n % 4 == 3) printf("\n");
    }
    
    uint32_t rom_size = buffer[124];
    uint32_t addr = 0;
    //card.resizeRom(rom_size); //resizing the rom breaks instrumentation tracking crashing the emulator.
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
            //for(int n=0; n<512; n++)
            //    card.updateRom(addr+n, image[sector * 512 + n]);
            addr += 512;
            sector++;
            count--;
        }
    }
}
