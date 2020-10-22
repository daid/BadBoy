#include "mbc.h"
#include <stdio.h>


uint32_t MBC1::mapRom(uint16_t address)
{
    if (address < 0x4000)
    {
        if (mode)
            return address | (low_rom_bank * 0x4000);
        return address;
    }
    return (address & 0x3fff) + high_rom_bank * 0x4000;
}

uint32_t MBC1::mapSRam(uint16_t address)
{
    return address + ram_bank * 0x2000;
}

void MBC1::writeRom(uint16_t address, uint8_t value)
{
    if (address >= 0x0000 && address < 0x2000)
    {
        ram_enabled = (value & 0x0F) == 0x0A;
    }
    else if (address >= 0x2000 && address < 0x4000)
    {
        value &= 0x1F;
        if (value == 0) value = 1;
        high_rom_bank = (high_rom_bank & 0xFFE0) | value;
    }
    else if (address >= 0x4000 && address < 0x6000)
    {
        if (mode)
        {
            value &= 0x03;
            low_rom_bank = (value << 5);
            high_rom_bank = (high_rom_bank & 0x001F) | (value << 5);
        } else {
            ram_bank = value;
        }
    }
    else if (address >= 0x6000 && address < 0x8000)
    {
        mode = value & 0x01;
    }
}

uint32_t MBC2::mapRom(uint16_t address)
{
    if (address < 0x4000)
        return address;
    return (address & 0x3fff) | rom_bank * 0x4000;
}

uint32_t MBC2::mapSRam(uint16_t address)
{
    return address & 0x01ff;
}

void MBC2::writeRom(uint16_t address, uint8_t value)
{
    if (address >= 0x0000 && address < 0x4000)
    {
        if (address & 0x0100)
        {
            rom_bank = value & 0x0f;
            if (value == 0) value = 1;
        }
        else
        {
            ram_enabled = (value & 0x0F) == 0x0A;
        }
    }
}

uint32_t MBC3::mapRom(uint16_t address)
{
    if (address < 0x4000)
        return address;
    return (address & 0x3fff) + rom_bank * 0x4000;
}

uint32_t MBC3::mapSRam(uint16_t address)
{
    return address + ram_bank * 0x2000;
}

void MBC3::writeRom(uint16_t address, uint8_t value)
{
    if (address >= 0x0000 && address < 0x2000)
        ram_enabled = value == 0x0A;
    else if (address >= 0x2000 && address < 0x4000)
        rom_bank = (rom_bank & 0xFF00) | value;
    else if (address >= 0x4000 && address < 0x6000)
        ram_bank = value; //TODO: RTC
}

uint32_t MBC5::mapRom(uint16_t address)
{
    if (address < 0x4000)
        return address;
    return (address & 0x3fff) + rom_bank * 0x4000;
}

uint32_t MBC5::mapSRam(uint16_t address)
{
    return address + ram_bank * 0x2000;
}

void MBC5::writeRom(uint16_t address, uint8_t value)
{
    if (address >= 0x0000 && address < 0x2000)
        ram_enabled = value == 0x0A;
    else if (address >= 0x2000 && address < 0x3000)
        rom_bank = (rom_bank & 0xFF00) | value;
    else if (address >= 0x3000 && address < 0x4000)
        rom_bank = (rom_bank & 0x00FF) | value;
    else if (address >= 0x4000 && address < 0x6000)
        ram_bank = value;
}
