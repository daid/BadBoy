#include <stdio.h>
#include "opcodes.h"
#include "mm.h"
#include "cpu.h"

static Mem8* dereference(Mem8& high, Mem8& low)
{
    uint16_t address = low.get() | high.get() << 8;
    high.markOrigin(MARK_PTR_HIGH);
    low.markOrigin(MARK_PTR_LOW);
    return &mm::get(address);
}

Opcode decode(uint16_t address)
{
    auto& m = mm::get(address);
    int op = m.get();
    if (op == 0xCB)
    {
        op = mm::get(address + 1).get();
        Opcode result{Opcode::ERROR, 2, 8};
        switch(op & 0x07)
        {
        case 0: result.dst_l = &cpu.B; break;
        case 1: result.dst_l = &cpu.C; break;
        case 2: result.dst_l = &cpu.D; break;
        case 3: result.dst_l = &cpu.E; break;
        case 4: result.dst_l = &cpu.H; break;
        case 5: result.dst_l = &cpu.L; break;
        case 6: result.dst_l = dereference(cpu.H, cpu.L); result.cycles = 16; break;
        case 7: result.dst_l = &cpu.A; break;
        }
        if (op < 0x40)
        {
            switch(op & 0xF8)
            {
            case 0x00: result.type = Opcode::RLC; break;
            case 0x08: result.type = Opcode::RRC; break;
            case 0x10: result.type = Opcode::RL; break;
            case 0x18: result.type = Opcode::RR; break;
            case 0x20: result.type = Opcode::SLA; break;
            case 0x28: result.type = Opcode::SRA; break;
            case 0x30: result.type = Opcode::SWAP; break;
            case 0x38: result.type = Opcode::SRL; break;
            }
        }else
        {
            result.value = (op >> 3) & 0x07;
            switch(op & 0xC0)
            {
            case 0x40: result.type = Opcode::BIT; if (result.cycles == 16) result.cycles = 12; break;
            case 0x80: result.type = Opcode::RES; break;
            case 0xC0: result.type = Opcode::SET; break;
            }
        }
        return result;
    }

    switch(op)
    {
    case 0x00: return {Opcode::NOP, 1, 4};
    case 0x10: return {Opcode::STOP, 1, 4};
    case 0x20: return {Opcode::JRNZ, 2, 8, nullptr, &mm::get(address + 1)};
    case 0x30: return {Opcode::JRNC, 2, 8, nullptr, &mm::get(address + 1)};
    
    case 0x01: return {Opcode::LD16, 3, 12, &cpu.B, &cpu.C, &mm::get(address + 2), &mm::get(address + 1)};
    case 0x11: return {Opcode::LD16, 3, 12, &cpu.D, &cpu.E, &mm::get(address + 2), &mm::get(address + 1)};
    case 0x21: return {Opcode::LD16, 3, 12, &cpu.H, &cpu.L, &mm::get(address + 2), &mm::get(address + 1)};
    case 0x31: return {Opcode::LD16, 3, 12, &cpu.S, &cpu.P, &mm::get(address + 2), &mm::get(address + 1)};

    case 0x02: return {Opcode::LD8, 1, 8, nullptr, dereference(cpu.B, cpu.C), nullptr, &cpu.A};
    case 0x12: return {Opcode::LD8, 1, 8, nullptr, dereference(cpu.D, cpu.E), nullptr, &cpu.A};
    case 0x22: return {Opcode::LD8, 1, 8, nullptr, &mm::get(cpu.getHLinc()), nullptr, &cpu.A};
    case 0x32: return {Opcode::LD8, 1, 8, nullptr, &mm::get(cpu.getHLdec()), nullptr, &cpu.A};

    case 0x03: return {Opcode::INC16, 1, 8, &cpu.B, &cpu.C};
    case 0x13: return {Opcode::INC16, 1, 8, &cpu.D, &cpu.E};
    case 0x23: return {Opcode::INC16, 1, 8, &cpu.H, &cpu.L};
    case 0x33: return {Opcode::INC16, 1, 8, &cpu.S, &cpu.P};

    case 0x04: return {Opcode::INC8, 1, 4, nullptr, &cpu.B};
    case 0x14: return {Opcode::INC8, 1, 4, nullptr, &cpu.D};
    case 0x24: return {Opcode::INC8, 1, 4, nullptr, &cpu.H};
    case 0x34: return {Opcode::INC8, 1, 12, nullptr, dereference(cpu.H, cpu.L)};

    case 0x05: return {Opcode::DEC8, 1, 4, nullptr, &cpu.B};
    case 0x15: return {Opcode::DEC8, 1, 4, nullptr, &cpu.D};
    case 0x25: return {Opcode::DEC8, 1, 4, nullptr, &cpu.H};
    case 0x35: return {Opcode::DEC8, 1, 12, nullptr, dereference(cpu.H, cpu.L)};

    case 0x06: return {Opcode::LD8, 2, 8, nullptr, &cpu.B, nullptr, &mm::get(address + 1)};
    case 0x16: return {Opcode::LD8, 2, 8, nullptr, &cpu.D, nullptr, &mm::get(address + 1)};
    case 0x26: return {Opcode::LD8, 2, 8, nullptr, &cpu.H, nullptr, &mm::get(address + 1)};
    case 0x36: return {Opcode::LD8, 2, 12, nullptr, dereference(cpu.H, cpu.L), nullptr, &mm::get(address + 1)};

    case 0x07: return {Opcode::RLCA, 1, 4, nullptr, &cpu.A};
    case 0x17: return {Opcode::RLA, 1, 4, nullptr, &cpu.A};
    case 0x27: return {Opcode::DAA, 1, 4, nullptr, &cpu.A};
    case 0x37: return {Opcode::SCF, 1, 4};

    case 0x08:{
            uint16_t a = mm::get(address + 2).get() << 8 | mm::get(address + 1).get();
            return {Opcode::LD16, 3, 20, &mm::get(a + 1), &mm::get(a), &cpu.S, &cpu.P};
        }
    case 0x18: return {Opcode::JR, 2, 12, nullptr, &mm::get(address + 1)};
    case 0x28: return {Opcode::JRZ, 2, 8, nullptr, &mm::get(address + 1)};
    case 0x38: return {Opcode::JRC, 2, 8, nullptr, &mm::get(address + 1)};

    case 0x09: return {Opcode::ADD16, 1, 8, &cpu.H, &cpu.L, &cpu.B, &cpu.C};
    case 0x19: return {Opcode::ADD16, 1, 8, &cpu.H, &cpu.L, &cpu.D, &cpu.E};
    case 0x29: return {Opcode::ADD16, 1, 8, &cpu.H, &cpu.L, &cpu.H, &cpu.L};
    case 0x39: return {Opcode::ADD16, 1, 8, &cpu.H, &cpu.L, &cpu.S, &cpu.P};

    case 0x0A: return {Opcode::LD8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.B, cpu.C)};
    case 0x1A: return {Opcode::LD8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.D, cpu.E)};
    case 0x2A: return {Opcode::LD8, 1, 8, nullptr, &cpu.A, nullptr, &mm::get(cpu.getHLinc())};
    case 0x3A: return {Opcode::LD8, 1, 8, nullptr, &cpu.A, nullptr, &mm::get(cpu.getHLdec())};

    case 0x0B: return {Opcode::DEC16, 1, 8, &cpu.B, &cpu.C};
    case 0x1B: return {Opcode::DEC16, 1, 8, &cpu.D, &cpu.E};
    case 0x2B: return {Opcode::DEC16, 1, 8, &cpu.H, &cpu.L};
    case 0x3B: return {Opcode::DEC16, 1, 8, &cpu.S, &cpu.P};

    case 0x0C: return {Opcode::INC8, 1, 4, nullptr, &cpu.C};
    case 0x1C: return {Opcode::INC8, 1, 4, nullptr, &cpu.E};
    case 0x2C: return {Opcode::INC8, 1, 4, nullptr, &cpu.L};
    case 0x3C: return {Opcode::INC8, 1, 4, nullptr, &cpu.A};

    case 0x0D: return {Opcode::DEC8, 1, 4, nullptr, &cpu.C};
    case 0x1D: return {Opcode::DEC8, 1, 4, nullptr, &cpu.E};
    case 0x2D: return {Opcode::DEC8, 1, 4, nullptr, &cpu.L};
    case 0x3D: return {Opcode::DEC8, 1, 4, nullptr, &cpu.A};

    case 0x0E: return {Opcode::LD8, 2, 8, nullptr, &cpu.C, nullptr, &mm::get(address + 1)};
    case 0x1E: return {Opcode::LD8, 2, 8, nullptr, &cpu.E, nullptr, &mm::get(address + 1)};
    case 0x2E: return {Opcode::LD8, 2, 8, nullptr, &cpu.L, nullptr, &mm::get(address + 1)};
    case 0x3E: return {Opcode::LD8, 2, 8, nullptr, &cpu.A, nullptr, &mm::get(address + 1)};

    case 0x0F: return {Opcode::RRCA, 1, 4, nullptr, &cpu.A};
    case 0x1F: return {Opcode::RRA, 1, 4, nullptr, &cpu.A};
    case 0x2F: return {Opcode::CPL, 1, 4, nullptr, &cpu.A};
    case 0x3F: return {Opcode::CCF, 1, 4};

    case 0x40: return {Opcode::LD8, 1, 4, nullptr, &cpu.B, nullptr, &cpu.B};
    case 0x50: return {Opcode::LD8, 1, 4, nullptr, &cpu.D, nullptr, &cpu.B};
    case 0x60: return {Opcode::LD8, 1, 4, nullptr, &cpu.H, nullptr, &cpu.B};
    case 0x70: return {Opcode::LD8, 1, 8, nullptr, dereference(cpu.H, cpu.L), nullptr, &cpu.B};

    case 0x41: return {Opcode::LD8, 1, 4, nullptr, &cpu.B, nullptr, &cpu.C};
    case 0x51: return {Opcode::LD8, 1, 4, nullptr, &cpu.D, nullptr, &cpu.C};
    case 0x61: return {Opcode::LD8, 1, 4, nullptr, &cpu.H, nullptr, &cpu.C};
    case 0x71: return {Opcode::LD8, 1, 8, nullptr, dereference(cpu.H, cpu.L), nullptr, &cpu.C};

    case 0x42: return {Opcode::LD8, 1, 4, nullptr, &cpu.B, nullptr, &cpu.D};
    case 0x52: return {Opcode::LD8, 1, 4, nullptr, &cpu.D, nullptr, &cpu.D};
    case 0x62: return {Opcode::LD8, 1, 4, nullptr, &cpu.H, nullptr, &cpu.D};
    case 0x72: return {Opcode::LD8, 1, 8, nullptr, dereference(cpu.H, cpu.L), nullptr, &cpu.D};

    case 0x43: return {Opcode::LD8, 1, 4, nullptr, &cpu.B, nullptr, &cpu.E};
    case 0x53: return {Opcode::LD8, 1, 4, nullptr, &cpu.D, nullptr, &cpu.E};
    case 0x63: return {Opcode::LD8, 1, 4, nullptr, &cpu.H, nullptr, &cpu.E};
    case 0x73: return {Opcode::LD8, 1, 8, nullptr, dereference(cpu.H, cpu.L), nullptr, &cpu.E};

    case 0x44: return {Opcode::LD8, 1, 4, nullptr, &cpu.B, nullptr, &cpu.H};
    case 0x54: return {Opcode::LD8, 1, 4, nullptr, &cpu.D, nullptr, &cpu.H};
    case 0x64: return {Opcode::LD8, 1, 4, nullptr, &cpu.H, nullptr, &cpu.H};
    case 0x74: return {Opcode::LD8, 1, 8, nullptr, dereference(cpu.H, cpu.L), nullptr, &cpu.H};

    case 0x45: return {Opcode::LD8, 1, 4, nullptr, &cpu.B, nullptr, &cpu.L};
    case 0x55: return {Opcode::LD8, 1, 4, nullptr, &cpu.D, nullptr, &cpu.L};
    case 0x65: return {Opcode::LD8, 1, 4, nullptr, &cpu.H, nullptr, &cpu.L};
    case 0x75: return {Opcode::LD8, 1, 8, nullptr, dereference(cpu.H, cpu.L), nullptr, &cpu.L};

    case 0x46: return {Opcode::LD8, 1, 8, nullptr, &cpu.B, nullptr, dereference(cpu.H, cpu.L)};
    case 0x56: return {Opcode::LD8, 1, 8, nullptr, &cpu.D, nullptr, dereference(cpu.H, cpu.L)};
    case 0x66: return {Opcode::LD8, 1, 8, nullptr, &cpu.H, nullptr, dereference(cpu.H, cpu.L)};
    case 0x76: return {Opcode::HALT, 1, 4};

    case 0x47: return {Opcode::LD8, 1, 4, nullptr, &cpu.B, nullptr, &cpu.A};
    case 0x57: return {Opcode::LD8, 1, 4, nullptr, &cpu.D, nullptr, &cpu.A};
    case 0x67: return {Opcode::LD8, 1, 4, nullptr, &cpu.H, nullptr, &cpu.A};
    case 0x77: return {Opcode::LD8, 1, 8, nullptr, dereference(cpu.H, cpu.L), nullptr, &cpu.A};

    case 0x48: return {Opcode::LD8, 1, 4, nullptr, &cpu.C, nullptr, &cpu.B};
    case 0x58: return {Opcode::LD8, 1, 4, nullptr, &cpu.E, nullptr, &cpu.B};
    case 0x68: return {Opcode::LD8, 1, 4, nullptr, &cpu.L, nullptr, &cpu.B};
    case 0x78: return {Opcode::LD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.B};

    case 0x49: return {Opcode::LD8, 1, 4, nullptr, &cpu.C, nullptr, &cpu.C};
    case 0x59: return {Opcode::LD8, 1, 4, nullptr, &cpu.E, nullptr, &cpu.C};
    case 0x69: return {Opcode::LD8, 1, 4, nullptr, &cpu.L, nullptr, &cpu.C};
    case 0x79: return {Opcode::LD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.C};

    case 0x4A: return {Opcode::LD8, 1, 4, nullptr, &cpu.C, nullptr, &cpu.D};
    case 0x5A: return {Opcode::LD8, 1, 4, nullptr, &cpu.E, nullptr, &cpu.D};
    case 0x6A: return {Opcode::LD8, 1, 4, nullptr, &cpu.L, nullptr, &cpu.D};
    case 0x7A: return {Opcode::LD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.D};

    case 0x4B: return {Opcode::LD8, 1, 4, nullptr, &cpu.C, nullptr, &cpu.E};
    case 0x5B: return {Opcode::LD8, 1, 4, nullptr, &cpu.E, nullptr, &cpu.E};
    case 0x6B: return {Opcode::LD8, 1, 4, nullptr, &cpu.L, nullptr, &cpu.E};
    case 0x7B: return {Opcode::LD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.E};

    case 0x4C: return {Opcode::LD8, 1, 4, nullptr, &cpu.C, nullptr, &cpu.H};
    case 0x5C: return {Opcode::LD8, 1, 4, nullptr, &cpu.E, nullptr, &cpu.H};
    case 0x6C: return {Opcode::LD8, 1, 4, nullptr, &cpu.L, nullptr, &cpu.H};
    case 0x7C: return {Opcode::LD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.H};

    case 0x4D: return {Opcode::LD8, 1, 4, nullptr, &cpu.C, nullptr, &cpu.L};
    case 0x5D: return {Opcode::LD8, 1, 4, nullptr, &cpu.E, nullptr, &cpu.L};
    case 0x6D: return {Opcode::LD8, 1, 4, nullptr, &cpu.L, nullptr, &cpu.L};
    case 0x7D: return {Opcode::LD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.L};

    case 0x4E: return {Opcode::LD8, 1, 8, nullptr, &cpu.C, nullptr, dereference(cpu.H, cpu.L)};
    case 0x5E: return {Opcode::LD8, 1, 8, nullptr, &cpu.E, nullptr, dereference(cpu.H, cpu.L)};
    case 0x6E: return {Opcode::LD8, 1, 8, nullptr, &cpu.L, nullptr, dereference(cpu.H, cpu.L)};
    case 0x7E: return {Opcode::LD8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.H, cpu.L)};

    case 0x4F: return {Opcode::LD8, 1, 4, nullptr, &cpu.C, nullptr, &cpu.A};
    case 0x5F: return {Opcode::LD8, 1, 4, nullptr, &cpu.E, nullptr, &cpu.A};
    case 0x6F: return {Opcode::LD8, 1, 4, nullptr, &cpu.L, nullptr, &cpu.A};
    case 0x7F: return {Opcode::LD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.A};

    case 0x80: return {Opcode::ADD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.B};
    case 0x81: return {Opcode::ADD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.C};
    case 0x82: return {Opcode::ADD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.D};
    case 0x83: return {Opcode::ADD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.E};
    case 0x84: return {Opcode::ADD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.H};
    case 0x85: return {Opcode::ADD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.L};
    case 0x86: return {Opcode::ADD8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.H, cpu.L)};
    case 0x87: return {Opcode::ADD8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.A};

    case 0x88: return {Opcode::ADC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.B};
    case 0x89: return {Opcode::ADC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.C};
    case 0x8A: return {Opcode::ADC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.D};
    case 0x8B: return {Opcode::ADC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.E};
    case 0x8C: return {Opcode::ADC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.H};
    case 0x8D: return {Opcode::ADC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.L};
    case 0x8E: return {Opcode::ADC8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.H, cpu.L)};
    case 0x8F: return {Opcode::ADC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.A};

    case 0x90: return {Opcode::SUB8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.B};
    case 0x91: return {Opcode::SUB8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.C};
    case 0x92: return {Opcode::SUB8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.D};
    case 0x93: return {Opcode::SUB8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.E};
    case 0x94: return {Opcode::SUB8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.H};
    case 0x95: return {Opcode::SUB8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.L};
    case 0x96: return {Opcode::SUB8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.H, cpu.L)};
    case 0x97: return {Opcode::SUB8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.A};

    case 0x98: return {Opcode::SBC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.B};
    case 0x99: return {Opcode::SBC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.C};
    case 0x9A: return {Opcode::SBC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.D};
    case 0x9B: return {Opcode::SBC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.E};
    case 0x9C: return {Opcode::SBC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.H};
    case 0x9D: return {Opcode::SBC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.L};
    case 0x9E: return {Opcode::SBC8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.H, cpu.L)};
    case 0x9F: return {Opcode::SBC8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.A};

    case 0xA0: return {Opcode::AND8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.B};
    case 0xA1: return {Opcode::AND8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.C};
    case 0xA2: return {Opcode::AND8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.D};
    case 0xA3: return {Opcode::AND8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.E};
    case 0xA4: return {Opcode::AND8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.H};
    case 0xA5: return {Opcode::AND8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.L};
    case 0xA6: return {Opcode::AND8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.H, cpu.L)};
    case 0xA7: return {Opcode::AND8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.A};

    case 0xA8: return {Opcode::XOR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.B};
    case 0xA9: return {Opcode::XOR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.C};
    case 0xAA: return {Opcode::XOR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.D};
    case 0xAB: return {Opcode::XOR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.E};
    case 0xAC: return {Opcode::XOR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.H};
    case 0xAD: return {Opcode::XOR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.L};
    case 0xAE: return {Opcode::XOR8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.H, cpu.L)};
    case 0xAF: return {Opcode::XOR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.A};

    case 0xB0: return {Opcode::OR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.B};
    case 0xB1: return {Opcode::OR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.C};
    case 0xB2: return {Opcode::OR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.D};
    case 0xB3: return {Opcode::OR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.E};
    case 0xB4: return {Opcode::OR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.H};
    case 0xB5: return {Opcode::OR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.L};
    case 0xB6: return {Opcode::OR8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.H, cpu.L)};
    case 0xB7: return {Opcode::OR8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.A};

    case 0xB8: return {Opcode::CP8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.B};
    case 0xB9: return {Opcode::CP8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.C};
    case 0xBA: return {Opcode::CP8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.D};
    case 0xBB: return {Opcode::CP8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.E};
    case 0xBC: return {Opcode::CP8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.H};
    case 0xBD: return {Opcode::CP8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.L};
    case 0xBE: return {Opcode::CP8, 1, 8, nullptr, &cpu.A, nullptr, dereference(cpu.H, cpu.L)};
    case 0xBF: return {Opcode::CP8, 1, 4, nullptr, &cpu.A, nullptr, &cpu.A};

    case 0xC0: return {Opcode::RETNZ, 1, 8};
    case 0xD0: return {Opcode::RETNC, 1, 8};
    case 0xE0: return {Opcode::LD8, 2, 12, nullptr, &mm::get(0xFF00 + mm::get(address + 1).get()), nullptr, &cpu.A};
    case 0xF0: return {Opcode::LD8, 2, 12, nullptr, &cpu.A, nullptr, &mm::get(0xFF00 + mm::get(address + 1).get())};

    case 0xC1: return {Opcode::POP16, 1, 12, &cpu.B, &cpu.C};
    case 0xD1: return {Opcode::POP16, 1, 12, &cpu.D, &cpu.E};
    case 0xE1: return {Opcode::POP16, 1, 12, &cpu.H, &cpu.L};
    case 0xF1: return {Opcode::POP16, 1, 12, &cpu.A, &cpu.F};

    case 0xC2: return {Opcode::JPNZ, 3, 8, &mm::get(address + 2), &mm::get(address + 1)};
    case 0xD2: return {Opcode::JPNC, 3, 8, &mm::get(address + 2), &mm::get(address + 1)};
    case 0xE2: return {Opcode::LD8, 1, 8, nullptr, &mm::get(0xFF00 + cpu.C.get()), nullptr, &cpu.A};
    case 0xF2: return {Opcode::LD8, 1, 8, nullptr, &cpu.A, nullptr, &mm::get(0xFF00 + cpu.C.get())};

    case 0xC3: return {Opcode::JP, 3, 16, &mm::get(address + 2), &mm::get(address + 1)};
    case 0xD3: return {Opcode::ERROR};
    case 0xE3: return {Opcode::ERROR};
    case 0xF3: return {Opcode::DI, 1, 4};

    case 0xC4: return {Opcode::CALLNZ, 3, 12, &mm::get(address + 2), &mm::get(address + 1)};
    case 0xD4: return {Opcode::CALLNC, 3, 12, &mm::get(address + 2), &mm::get(address + 1)};
    case 0xE4: return {Opcode::ERROR};
    case 0xF4: return {Opcode::ERROR};

    case 0xC5: return {Opcode::PUSH16, 1, 16, &cpu.B, &cpu.C};
    case 0xD5: return {Opcode::PUSH16, 1, 16, &cpu.D, &cpu.E};
    case 0xE5: return {Opcode::PUSH16, 1, 16, &cpu.H, &cpu.L};
    case 0xF5: return {Opcode::PUSH16, 1, 16, &cpu.A, &cpu.F};

    case 0xC6: return {Opcode::ADD8, 2, 8, nullptr, &cpu.A, nullptr, &mm::get(address + 1)};
    case 0xD6: return {Opcode::SUB8, 2, 8, nullptr, &cpu.A, nullptr, &mm::get(address + 1)};
    case 0xE6: return {Opcode::AND8, 2, 8, nullptr, &cpu.A, nullptr, &mm::get(address + 1)};
    case 0xF6: return {Opcode::OR8, 2, 8, nullptr, &cpu.A, nullptr, &mm::get(address + 1)};

    case 0xC7: return {Opcode::RST, 1, 16, nullptr, nullptr, nullptr, nullptr, 0x00};
    case 0xD7: return {Opcode::RST, 1, 16, nullptr, nullptr, nullptr, nullptr, 0x10};
    case 0xE7: return {Opcode::RST, 1, 16, nullptr, nullptr, nullptr, nullptr, 0x20};
    case 0xF7: return {Opcode::RST, 1, 16, nullptr, nullptr, nullptr, nullptr, 0x30};

    case 0xC8: return {Opcode::RETZ, 1, 8};
    case 0xD8: return {Opcode::RETC, 1, 8};
    case 0xE8: return {Opcode::ADD8TO16, 2, 16, &cpu.S, &cpu.P, nullptr, &mm::get(address + 1)};
    case 0xF8: return {Opcode::LDSPADD8, 2, 12, &cpu.H, &cpu.L, nullptr, &mm::get(address + 1)};

    case 0xC9: return {Opcode::RET, 1, 16};
    case 0xD9: return {Opcode::RETI, 1, 16};
    case 0xE9: return {Opcode::JP, 1, 4, &cpu.H, &cpu.L};
    case 0xF9: return {Opcode::LD16, 1, 8, &cpu.S, &cpu.P, &cpu.H, &cpu.L};

    case 0xCA: return {Opcode::JPZ, 3, 12, &mm::get(address + 2), &mm::get(address + 1)};
    case 0xDA: return {Opcode::JPC, 3, 12, &mm::get(address + 2), &mm::get(address + 1)};
    case 0xEA: return {Opcode::LD8, 3, 16, nullptr, &mm::get(mm::get(address + 2).get() << 8 | mm::get(address + 1).get()), nullptr, &cpu.A};
    case 0xFA: return {Opcode::LD8, 3, 16, nullptr, &cpu.A, nullptr, &mm::get(mm::get(address + 2).get() << 8 | mm::get(address + 1).get())};

    case 0xCB: return {Opcode::ERROR};
    case 0xDB: return {Opcode::ERROR};
    case 0xEB: return {Opcode::ERROR};
    case 0xFB: return {Opcode::EI, 1, 4};

    case 0xCC: return {Opcode::CALLZ, 3, 12, &mm::get(address + 2), &mm::get(address + 1)};
    case 0xDC: return {Opcode::CALLC, 3, 12, &mm::get(address + 2), &mm::get(address + 1)};
    case 0xEC: return {Opcode::ERROR};
    case 0xFC: return {Opcode::ERROR};

    case 0xCD: return {Opcode::CALL, 3, 24, &mm::get(address + 2), &mm::get(address + 1)};
    case 0xDD: return {Opcode::ERROR};
    case 0xED: return {Opcode::ERROR};
    case 0xFD: return {Opcode::ERROR};

    case 0xCE: return {Opcode::ADC8, 2, 8, nullptr, &cpu.A, nullptr, &mm::get(address + 1)};
    case 0xDE: return {Opcode::SBC8, 2, 8, nullptr, &cpu.A, nullptr, &mm::get(address + 1)};
    case 0xEE: return {Opcode::XOR8, 2, 8, nullptr, &cpu.A, nullptr, &mm::get(address + 1)};
    case 0xFE: return {Opcode::CP8, 2, 8, nullptr, &cpu.A, nullptr, &mm::get(address + 1)};

    case 0xCF: return {Opcode::RST, 1, 16, nullptr, nullptr, nullptr, nullptr, 0x08};
    case 0xDF: return {Opcode::RST, 1, 16, nullptr, nullptr, nullptr, nullptr, 0x18};
    case 0xEF: return {Opcode::RST, 1, 16, nullptr, nullptr, nullptr, nullptr, 0x28};
    case 0xFF: return {Opcode::RST, 1, 16, nullptr, nullptr, nullptr, nullptr, 0x38};
    }

    return {Opcode::ERROR};
}
