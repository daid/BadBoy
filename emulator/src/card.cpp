#include "card.h"
#include "input.h"
#include "ram.h"
#include <stdio.h>

Card card;


class Mem8Rom : public Mem8
{
public:
    uint8_t value;

    uint8_t get() const override
    {
        return value;
    }

    void setImpl(uint8_t value) override
    {
        if (id < 0x4000)
            card.mbc->writeRom(id, value);
        else
            card.mbc->writeRom((id & 0x3fff) | 0x4000, value);
    }
};

static Mem8Block<Mem8Rom> bootrom;
static Mem8Block<Mem8Rom> rom;
static Mem8Block<Mem8Ram> sram;


void Card::init()
{
    bootrom.resize(0x100);
    sram.resize(0x8000);
    for(uint32_t n=0; n<0x100; n++)
        bootrom[n].id = n | ID_ROM;
    for(uint32_t n=0; n<sram.size(); n++)
        sram[n].id = n | ID_SRAM;

    FILE* f = fopen("dmg_boot.bin", "rb");
    if (f)
    {
        uint32_t n = 0;
        while(fread(&bootrom[n].value, sizeof(uint8_t), sizeof(uint8_t), f) > 0)
        {
            n += 1;
        }
        fclose(f);
    }

    if (rom.size() == 0)
    {
        uint32_t size = 0x8000;
        rom.resize(size);
        for(uint32_t n=0; n<size; n++)
        {
            rom[n].id = n | ID_ROM;
            rom[n].value = 0xDD;
        }
        for(uint32_t n=0x104; n<0x134; n++)
            rom[n].value = bootrom[n-0x104+0xA8].value;
        rom[0x143].value = 0x00;
        uint8_t checksum = 0;
        for(uint32_t n=0x134; n<0x14D; n++)
            checksum -= rom[n].value + 1;
        rom[0x14D].value = checksum;
    }
}

bool Card::load(const char* filename)
{
    FILE* f = fopen(filename, "rb");
    if (!f)
    {
        printf("Failed to open '%s'\n", filename);
        return false;
    }
    
    fseek(f, 0, SEEK_END);
    uint32_t size = ftell(f);
    uint32_t rom_bank_mask = 1;
    while(uint32_t(rom_bank_mask + 1) * 0x4000 < size)
        rom_bank_mask = (rom_bank_mask << 1) | 0x01;
    size = (rom_bank_mask + 1) * 0x4000;
    rom.resize(size);
    fseek(f, 0, SEEK_SET);
    for(uint32_t n=0; n<size; n++)
        rom[n].id = n | ID_ROM;

    uint32_t n = 0;
    while(fread(&rom[n].value, sizeof(uint8_t), sizeof(uint8_t), f) > 0)
    {
        n += 1;
    }

    mbc = std::make_unique<MBCNone>();
    switch(rom[0x147].value)
    {
    case 0x00:
        break;
    case 0x01:
    case 0x02:
    case 0x03:
        mbc = std::make_unique<MBC1>();
        break;
    case 0x05:
    case 0x06:
        mbc = std::make_unique<MBC2>();
        break;
    case 0x08:
    case 0x09:
        break;
    case 0x0b:
    case 0x0c:
    case 0x0d:
        //mbc = std::make_unique<MMM01>();
        break;
    case 0x0f:
    case 0x10:
        mbc = std::make_unique<MBC3RTC>();
        break;
    case 0x11:
    case 0x12:
    case 0x13:
        mbc = std::make_unique<MBC3>();
        break;
    case 0x19:
    case 0x1a:
    case 0x1b:
    case 0x1c://rumble pack?
    case 0x1d://rumble pack?
    case 0x1e://rumble pack?
        mbc = std::make_unique<MBC5>();
        break;
    case 0x20:
        //mbc = std::make_unique<MBC6>();
        break;
    case 0x22:
        //mbc = std::make_unique<MBC7>();
        break;
    }
    printf("Card type: %02x: %s\n", rom[0x147].value, typeid(*mbc.get()).name());

    fclose(f);
    return true;
}

Mem8& Card::getRom(uint16_t address)
{
    uint32_t rom_address = mbc->mapRom(address);
    return rom[rom_address % rom.size()];
}

Mem8& Card::getSRam(uint16_t address)
{
    uint32_t sram_address = mbc->mapSRam(address);
    return sram[sram_address % sram.size()];
}

Mem8& Card::getBoot(uint16_t address)
{
    return bootrom[address];
}

void Card::dumpInstrumentation(FILE* f)
{
    rom.dumpInstrumentation(f);
    sram.dumpInstrumentation(f);
}
