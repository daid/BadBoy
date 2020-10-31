#pragma once

#include "mem8.h"
#include "opcodes.h"

class Mem8Reg : public Mem8
{
public:
    uint8_t value;

    uint8_t get() const override
    {
        return value;
    }

    void setImpl(uint8_t value) override
    {
        this->value = value;
    }
};
class Mem8RegF : public Mem8
{
public:
    bool Z, N, H, C;

    uint8_t get() const override
    {
        uint8_t res = 0;
        if (Z) res |= 0x80;
        if (N) res |= 0x40;
        if (H) res |= 0x20;
        if (C) res |= 0x10;
        return res;
    }

    void setImpl(uint8_t value) override
    {
        Z = (value & 0x80);
        N = (value & 0x40);
        H = (value & 0x20);
        C = (value & 0x10);
    }
};


class Cpu
{
public:
    Mem8Reg A;
    Mem8RegF F;
    Mem8Reg B;
    Mem8Reg C;
    Mem8Reg D;
    Mem8Reg E;
    Mem8Reg H;
    Mem8Reg L;

    Mem8Reg S;
    Mem8Reg P;

    uint16_t pc;
    uint32_t cycles;
    uint32_t speed = 1;
    bool ime;
    bool halt;

    Mem8Reg IF;
    Mem8Reg IE;
    Mem8Reg KEY1;

    bool gbc;

    uint16_t getBC() const;
    uint16_t getDE() const;
    uint16_t getHL() const;
    uint16_t getSP() const;
    void setSP(uint16_t sp);

    uint16_t getHLinc();
    uint16_t getHLdec();

    void reset();
    void execute(const Opcode& opcode);
    void setInterrupt(uint8_t mask);
    void interrupt(uint16_t vector);
};
extern Cpu cpu;
