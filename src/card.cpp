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
        if (id >= 0x2000 && id < 0x4000)
        {
            if (value == 0)
                value = 1;
            card.rom_upper_bank = value & card.rom_bank_mask;
        }
        if (id >= 0x4000 && (id & 0x2000) == 0x0000)
        {
            card.ram_bank = value & 0x03;
        }
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

    //TODO: We currently emulate a MBC5+RAM, which should be compattible with most things.
    //      But from the header we can read which MBC we should be using.
    printf("Card type: %02x\n", rom[0x147].value);
    fclose(f);
    return true;
}

Mem8& Card::getRom(uint16_t address)
{
    if (address >= 0x4000)
        return rom[rom_upper_bank * 0x4000 + (address & 0x3FFF)];
    return rom[address];
}

Mem8& Card::getSRam(uint16_t address)
{
    return sram[ram_bank * 0x2000 + address];
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
