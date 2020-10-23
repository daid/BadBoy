#include "ezflash.h"
#include "card.h"
#include "cpu.h"
#include "input.h"

#include <stdio.h>
#include <assert.h>


EZFlashMBC::EZFlashMBC(const char* image_filename)
{
    FILE* f = fopen(image_filename, "rb");
    fseek(f, 0, SEEK_END);
    image.resize(ftell(f));
    fseek(f, 0, SEEK_SET);
    if (fread(image.data(), 1, image.size(), f) != image.size())
        printf("Failed to read sd card image...\n");
    fclose(f);
}

uint32_t EZFlashMBC::mapRom(uint16_t address)
{
    if (address < 0x4000)
        return address;
    return (address & 0x3fff) | rom_bank * 0x4000;
}

uint32_t EZFlashMBC::mapSRam(uint16_t address)
{
    //if (address == 0x0000) printf("  SRAM access\n");
    return address;
}

void EZFlashMBC::writeRom(uint16_t address, uint8_t value)
{
    if (address == 0x2000)
    {
        //The EZFlash seems to write 0xFF to the bank number but then never accesses the top bank.
        // But it seems to default to bank 0x01
        if (value == 0xff)
            value = 0x01;
        rom_bank = value;
    } else if (address == 0x7f00) {
        if (value == 0xE1) unlock = 1; else unlock = 0;
    } else if (address == 0x7f10) {
        if (value == 0xE2 && unlock == 1) unlock = 2; else unlock = 0;
    } else if (address == 0x7f20) {
        if (value == 0xE3 && unlock == 2) { unlock = 3; } else unlock = 0;
    } else if (address == 0x7f30 && unlock == 3) {
        //"SD" commands?
        //printf("Switch SRAM target: %02x\n", value);
        switch(value)
        {
        case 0: //Normal SRAM?
            break;
        case 1: //SD card sector data
            for(int n=0; n<512; n++)
                card.getSRam(n).set(image[n + image_sector_nr * 512]);
            break;
        case 3: // SD card command state?
            card.getSRam(0).set(0x01);
            break;
        }
    } else if (address == 0x7f36 && unlock == 3) {
        //"ROM" commands?
        printf("Switch SRAM target2: %02x\n", value);
        switch(value)
        {
        case 3: // command state?
            card.getSRam(0).set(0x02);
            break;
        }
    } else if (address == 0x7fb0 && unlock == 3) {
        image_sector_nr = value;
    } else if (address == 0x7fb1 && unlock == 3) {
        image_sector_nr |= value << 8;
    } else if (address == 0x7fb2 && unlock == 3) {
        image_sector_nr |= value << 16;
    } else if (address == 0x7fb3 && unlock == 3) {
        image_sector_nr |= value << 24;
    } else if (address == 0x7fb4 && unlock == 3) {
        image_sector_count = value; // unsure, only seen value 1 so far.
        printf("Accessing SD Sector: %08x:%02x\n", image_sector_nr, image_sector_count);
    } else if (address == 0x7fe0 && unlock == 3) {
        if (value == 0x80)
        {
            //Start loaded rom (should reset)
            input.quit = true;
        }
    } else if (address == 0x7ff0) {
        if (value == 0xE4 && unlock == 3) {
            //printf("LOCK/EXEC?\n");
        }
        unlock = 0;
    } else {
        printf("EZFlash ROM Write: %04x:%02x from %02x:%04x\n", address, value, cpu.pc >= 0x4000 ? rom_bank : 0, cpu.pc);
    }
}

uint32_t EZFlashMBC::getRomBankNr()
{
    return rom_bank;
}
