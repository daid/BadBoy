#pragma once

#include <stdint.h>

class MBC
{
public:
    virtual uint32_t mapRom(uint16_t address) = 0;
    virtual uint32_t mapSRam(uint16_t address) = 0;
    virtual void writeRom(uint16_t address, uint8_t value) = 0;
    virtual uint32_t getRomBankNr() = 0;
    virtual bool sramEnabled() = 0;
};

class MBCNone : public MBC
{
public:
    virtual uint32_t mapRom(uint16_t address) { return address; }
    virtual uint32_t mapSRam(uint16_t address) { return address; }
    virtual void writeRom(uint16_t address, uint8_t value) {}
    virtual uint32_t getRomBankNr() { return 1; }
    virtual bool sramEnabled() { return true; }
};

class MBC1 : public MBC
{
public:
    virtual uint32_t mapRom(uint16_t address) override;
    virtual uint32_t mapSRam(uint16_t address) override;
    virtual void writeRom(uint16_t address, uint8_t value) override;
    virtual uint32_t getRomBankNr() { return high_rom_bank; }
    virtual bool sramEnabled() { return ram_enabled; }

private:
    bool ram_enabled = false;
    uint16_t low_rom_bank = 0x00;
    uint16_t high_rom_bank = 0x01;
    uint16_t ram_bank = 0x00;
    uint8_t mode = 0;
};

class MBC2 : public MBC
{
public:
    virtual uint32_t mapRom(uint16_t address) override;
    virtual uint32_t mapSRam(uint16_t address) override;
    virtual void writeRom(uint16_t address, uint8_t value) override;
    virtual uint32_t getRomBankNr() { return rom_bank; }
    virtual bool sramEnabled() { return ram_enabled; }

private:
    bool ram_enabled = false;
    uint16_t rom_bank = 0x01;
};

class MBC3 : public MBC
{
public:
    virtual uint32_t mapRom(uint16_t address) override;
    virtual uint32_t mapSRam(uint16_t address) override;
    virtual void writeRom(uint16_t address, uint8_t value) override;
    virtual uint32_t getRomBankNr() { return rom_bank; }
    virtual bool sramEnabled() { return ram_enabled; }

private:
    bool ram_enabled = false;
    uint16_t rom_bank = 0x01;
    uint16_t ram_bank = 0x00;
};

class MBC3RTC : public MBC3
{
public:
};

class MBC5 : public MBC
{
public:
    virtual uint32_t mapRom(uint16_t address) override;
    virtual uint32_t mapSRam(uint16_t address) override;
    virtual void writeRom(uint16_t address, uint8_t value) override;
    virtual uint32_t getRomBankNr() { return rom_bank; }
    virtual bool sramEnabled() { return ram_enabled; }

private:
    bool ram_enabled = false;
    uint16_t rom_bank = 0x01;
    uint16_t ram_bank = 0x00;
};
/*
class MBC6 : public MBC
{
public:
    virtual uint32_t mapRom(uint16_t address) override;
    virtual uint32_t mapSRam(uint16_t address) override;
    virtual void writeRom(uint16_t address, uint8_t value) override;
    virtual uint32_t getRomBankNr() { return rom_bank; }
    virtual bool sramEnabled() { return ram_enabled; }

private:
    bool ram_enabled = false;
    uint16_t rom_bank = 0x01;
    uint16_t ram_bank = 0x00;
};

class MBC7 : public MBC
{
public:
    virtual uint32_t mapRom(uint16_t address) override;
    virtual uint32_t mapSRam(uint16_t address) override;
    virtual void writeRom(uint16_t address, uint8_t value) override;
    virtual uint32_t getRomBankNr() { return rom_bank; }
    virtual bool sramEnabled() { return ram_enabled; }

private:
    bool ram_enabled = false;
    uint16_t rom_bank = 0x01;
    uint16_t ram_bank = 0x00;
};

class MMM01 : public MBC
{
public:
    virtual uint32_t mapRom(uint16_t address) override;
    virtual uint32_t mapSRam(uint16_t address) override;
    virtual void writeRom(uint16_t address, uint8_t value) override;
    virtual uint32_t getRomBankNr() { return rom_bank; }
    virtual bool sramEnabled() { return ram_enabled; }

private:
    bool ram_enabled = false;
    uint16_t rom_bank = 0x01;
    uint16_t ram_bank = 0x00;
};
*/