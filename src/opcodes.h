#pragma once

#include <stdint.h>
#include "mem8.h"

struct Opcode
{
    enum Type
    {
        NOP,
        STOP,
        HALT,
        DI,
        EI,

        LD8,
        LD16,
        INC8,
        INC16,
        DEC8,
        DEC16,
        ADD8,
        ADC8,
        ADD16,
        SUB8,
        SBC8,
        AND8,
        XOR8,
        OR8,
        CP8,

        JR,
        JRZ,
        JRC,
        JRNZ,
        JRNC,

        JP,
        JPZ,
        JPC,
        JPNZ,
        JPNC,

        CALL,
        CALLZ,
        CALLC,
        CALLNZ,
        CALLNC,

        PUSH16,
        POP16,

        RET,
        RETZ,
        RETC,
        RETNZ,
        RETNC,
        RETI,

        RLCA,
        RLA,
        RRCA,
        RRA,

        DAA,
        SCF,
        CPL,
        CCF,

        ADD8TO16,
        LDSPADD8,
        RST,

        RLC,
        RRC,
        RL,
        RR,
        SLA,
        SRA,
        SWAP,
        SRL,

        BIT,
        RES,
        SET,

        ERROR,
    } type;
    int size = 1;
    int cycles = 4;
    Mem8* dst_h = nullptr;
    Mem8* dst_l = nullptr;
    Mem8* src_h = nullptr;
    Mem8* src_l = nullptr;
    int value = 0;
};

Opcode decode(uint16_t address);
