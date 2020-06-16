#include <stdio.h>
#include <unistd.h>

#include "cpu.h"
#include "mm.h"

Cpu cpu;

uint16_t Cpu::getBC() const
{
    return B.get() << 8 | C.get();
}

uint16_t Cpu::getDE() const
{
    return D.get() << 8 | E.get();
}

uint16_t Cpu::getHL() const
{
    return H.get() << 8 | L.get();
}

uint16_t Cpu::getSP() const
{
    return S.get() << 8 | P.get();
}

void Cpu::setSP(uint16_t sp)
{
    S.set(sp >> 8);
    P.set(sp);
}

uint16_t Cpu::getHLinc()
{
    uint16_t result = getHL() + 1;
    H.set(result >> 8);
    L.set(result);
    return result - 1;
}

uint16_t Cpu::getHLdec()
{
    uint16_t result = getHL() - 1;
    H.set(result >> 8);
    L.set(result);
    return result + 1;
}

#define NOT_IMPLEMENTED() do { printf("Not implemented instruction: %d at %s:%d\n", opcode.type, __FILE__, __LINE__); system("pause"); } while(0)

void Cpu::execute(const Opcode& opcode)
{
    for(uint16_t n=pc; n<pc+opcode.size; n++)
        mm::get(n).mark(MARK_INSTR);
    uint8_t tmp;
    pc += opcode.size;
    cycles += opcode.cycles;
    switch(opcode.type)
    {
    case Opcode::NOP: break;
    case Opcode::STOP: NOT_IMPLEMENTED(); break;
    case Opcode::HALT:
        halt = true;
        break;
    case Opcode::DI: ime = false; break;
    case Opcode::EI: ime = true; break;

    case Opcode::LD8:
        opcode.src_l->mark(MARK_DATA);
        opcode.dst_l->set(*opcode.src_l);
        break;
    case Opcode::LD16:
        opcode.dst_h->set(*opcode.src_h);
        opcode.dst_l->set(*opcode.src_l);
        break;
    case Opcode::INC8:
        opcode.dst_l->set(opcode.dst_l->get() + 1);
        F.Z = opcode.dst_l->get() == 0;
        F.N = false;
        F.H = (opcode.dst_l->get() & 0x0F) == 0x00;
        break;
    case Opcode::INC16:
        opcode.dst_l->set(opcode.dst_l->get() + 1);
        if (opcode.dst_l->get() == 0)
            opcode.dst_h->set(opcode.dst_h->get() + 1);
        break;
    case Opcode::DEC8:
        opcode.dst_l->set(opcode.dst_l->get() - 1);
        F.Z = opcode.dst_l->get() == 0;
        F.N = true;
        F.H = (opcode.dst_l->get() & 0x0F) == 0x0F;
        break;
    case Opcode::DEC16:
        opcode.dst_l->set(opcode.dst_l->get() - 1);
        if (opcode.dst_l->get() == 0xFF)
            opcode.dst_h->set(opcode.dst_h->get() - 1);
        break;
    case Opcode::ADD8:
        tmp = opcode.dst_l->get() + opcode.src_l->get();
        F.Z = tmp == 0x00;
        F.N = false;
        F.H = (tmp & 0x0F) < (opcode.dst_l->get() & 0x0F);
        F.C = (opcode.dst_l->get() + opcode.src_l->get()) > 0xFF;
        opcode.dst_l->set(tmp);
        break;
    case Opcode::ADC8:
        if (F.C)
        {
            tmp = opcode.dst_l->get() + opcode.src_l->get() + 1;
            F.H = (tmp & 0x0F) < (opcode.dst_l->get() & 0x0F) + 1;
            F.C = (opcode.dst_l->get() + opcode.src_l->get()) > 0xFE;
        }else{
            tmp = opcode.dst_l->get() + opcode.src_l->get();
            F.H = (tmp & 0x0F) < (opcode.dst_l->get() & 0x0F);
            F.C = (opcode.dst_l->get() + opcode.src_l->get()) > 0xFF;
        }
        F.Z = tmp == 0x00;
        F.N = false;
        opcode.dst_l->set(tmp);
        break;
    case Opcode::ADD16:{
        int dst = opcode.dst_l->get() | opcode.dst_h->get() << 8;
        int src = opcode.src_l->get() | opcode.src_h->get() << 8;
        int res = dst + src;
        F.H = (dst & 0xFFF) > (res & 0xFFF);
        F.N = false;
        F.C = res > 0xFFFF;
        opcode.dst_l->set(res);
        opcode.dst_h->set(res >> 8);
        }break;
    case Opcode::SUB8:
        tmp = opcode.dst_l->get() - opcode.src_l->get();
        F.Z = tmp == 0x00;
        F.N = true;
        F.H = (tmp & 0x0F) > (opcode.dst_l->get() & 0x0F);
        F.C = opcode.dst_l->get() < opcode.src_l->get();
        opcode.dst_l->set(tmp);
        break;
    case Opcode::SBC8:{
        int carry = F.C ? 1 : 0;
        int value = int(opcode.dst_l->get()) - int(opcode.src_l->get()) - carry;
        F.Z = (value & 0xFF) == 0x00;
        F.N = true;
        F.H = int(opcode.dst_l->get() & 0x0F) - (value & 0x0F) - carry < 0;
        F.C = value < 0;
        opcode.dst_l->set(value);
        }break;
    case Opcode::AND8:
        opcode.dst_l->set(opcode.dst_l->get() & opcode.src_l->get());
        F.Z = opcode.dst_l->get() == 0x00;
        F.N = false;
        F.H = true;
        F.C = false;
        break;
    case Opcode::XOR8:
        opcode.dst_l->set(opcode.dst_l->get() ^ opcode.src_l->get());
        F.Z = opcode.dst_l->get() == 0x00;
        F.N = F.H = F.C = false;
        break;
    case Opcode::OR8:
        opcode.dst_l->set(opcode.dst_l->get() | opcode.src_l->get());
        F.Z = opcode.dst_l->get() == 0x00;
        F.N = F.H = F.C = false;
        break;
    case Opcode::CP8:
        tmp = opcode.dst_l->get() - opcode.src_l->get();
        F.Z = tmp == 0x00;
        F.N = true;
        F.H = (tmp & 0x0F) > (opcode.dst_l->get() & 0x0F);
        F.C = opcode.dst_l->get() < opcode.src_l->get();
        break;

    case Opcode::JR: pc += static_cast<int8_t>(opcode.dst_l->get()); break;
    case Opcode::JRZ: if (F.Z) { pc += static_cast<int8_t>(opcode.dst_l->get()); cycles += 4; } break;
    case Opcode::JRC: if (F.C) { pc += static_cast<int8_t>(opcode.dst_l->get()); cycles += 4; } break;
    case Opcode::JRNZ: if (!F.Z) { pc += static_cast<int8_t>(opcode.dst_l->get()); cycles += 4; } break;
    case Opcode::JRNC: if (!F.C) { pc += static_cast<int8_t>(opcode.dst_l->get()); cycles += 4; } break;

    case Opcode::JP:
        opcode.dst_l->markOrigin(MARK_PTR);
        pc = (opcode.dst_h->get() << 8) | opcode.dst_l->get();
        break;
    case Opcode::JPZ: if (F.Z) { pc = (opcode.dst_h->get() << 8) | opcode.dst_l->get(); cycles += 4; } break;
    case Opcode::JPC: if (F.C) { pc = (opcode.dst_h->get() << 8) | opcode.dst_l->get(); cycles += 4; } break;
    case Opcode::JPNZ: if (!F.Z) { pc = (opcode.dst_h->get() << 8) | opcode.dst_l->get(); cycles += 4; } break;
    case Opcode::JPNC: if (!F.C) { pc = (opcode.dst_h->get() << 8) | opcode.dst_l->get(); cycles += 4; } break;

    case Opcode::CALL:
        mm::get(getSP() - 1).set(pc >> 8);
        mm::get(getSP() - 2).set(pc);
        setSP(getSP() - 2);
        pc = (opcode.dst_h->get() << 8) | opcode.dst_l->get();
        break;
    case Opcode::CALLZ:
        if (F.Z)
        {
            mm::get(getSP() - 1).set(pc >> 8);
            mm::get(getSP() - 2).set(pc);
            setSP(getSP() - 2);
            pc = (opcode.dst_h->get() << 8) | opcode.dst_l->get();
            cycles += 12;
        }
        break;
    case Opcode::CALLC:
        if (F.C)
        {
            mm::get(getSP() - 1).set(pc >> 8);
            mm::get(getSP() - 2).set(pc);
            setSP(getSP() - 2);
            pc = (opcode.dst_h->get() << 8) | opcode.dst_l->get();
            cycles += 12;
        }
        break;
    case Opcode::CALLNZ:
        if (!F.Z)
        {
            mm::get(getSP() - 1).set(pc >> 8);
            mm::get(getSP() - 2).set(pc);
            setSP(getSP() - 2);
            pc = (opcode.dst_h->get() << 8) | opcode.dst_l->get();
            cycles += 12;
        }
        break;
    case Opcode::CALLNC:
        if (!F.C)
        {
            mm::get(getSP() - 1).set(pc >> 8);
            mm::get(getSP() - 2).set(pc);
            setSP(getSP() - 2);
            pc = (opcode.dst_h->get() << 8) | opcode.dst_l->get();
            cycles += 12;
        }
        break;

    case Opcode::PUSH16:
        mm::get(getSP() - 1).set(opcode.dst_h->get());
        mm::get(getSP() - 2).set(opcode.dst_l->get());
        setSP(getSP() - 2);
        break;
    case Opcode::POP16:
        opcode.dst_l->set(mm::get(getSP()).get());
        opcode.dst_h->set(mm::get(getSP() + 1).get());
        setSP(getSP() + 2);
        break;

    case Opcode::RET:
        pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
        setSP(getSP() + 2);
        break;
    case Opcode::RETZ:
        if (F.Z)
        {
            pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
            setSP(getSP() + 2);
            cycles += 12;
        }
        break;
    case Opcode::RETC:
        if (F.C)
        {
            pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
            setSP(getSP() + 2);
            cycles += 12;
        }
        break;
    case Opcode::RETNZ:
        if (!F.Z)
        {
            pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
            setSP(getSP() + 2);
            cycles += 12;
        }
        break;
    case Opcode::RETNC:
        if (!F.C)
        {
            pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
            setSP(getSP() + 2);
            cycles += 12;
        }
        break;
    case Opcode::RETI:
        pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
        setSP(getSP() + 2);
        ime = true;
        break;


    case Opcode::RLCA:
        tmp = opcode.dst_l->get();
        F.C = tmp & 0x80;
        opcode.dst_l->set((tmp << 1) | (tmp >> 7));
        F.Z = F.N = F.H = false;
        break;
    case Opcode::RLA:
        tmp = opcode.dst_l->get();
        if (F.C)
            opcode.dst_l->set((tmp << 1) | 0x01);
        else
            opcode.dst_l->set((tmp << 1));
        F.Z = F.N = F.H = false;
        F.C = tmp & 0x80;
        break;
    case Opcode::RRCA:
        tmp = opcode.dst_l->get();
        tmp = (tmp >> 1) | (tmp << 7);
        opcode.dst_l->set(tmp);
        F.Z = F.N = F.H = false;
        F.C = tmp & 0x80;
        break;
    case Opcode::RRA:
        tmp = opcode.dst_l->get();
        if (F.C)
            opcode.dst_l->set((tmp >> 1) | 0x80);
        else
            opcode.dst_l->set((tmp >> 1));
        F.Z = F.N = F.H = false;
        F.C = tmp & 0x01;
        break;

    case Opcode::DAA:
        tmp = opcode.dst_l->get();
        if (!F.N)
        {
            if (F.C || tmp > 0x99)
            {
                tmp = tmp + 0x60;
                F.C = true;
            }
            if (F.H || (tmp & 0x0F) > 0x09)
            {
                tmp = tmp + 0x06;
                F.H = false;
            }
        }
        else if (F.C && F.H)
        {
            tmp += 0x9A;
            F.H = false;
        }
        else if (F.C)
        {
            tmp += 0xA0;
        }
        else if (F.H)
        {
            tmp += 0xFA;
            F.H = false;
        }
        F.Z = tmp == 0x00;
        opcode.dst_l->set(tmp);
        break;
    case Opcode::SCF:
        F.N = false;
        F.H = false;
        F.C = true;
        break;
    case Opcode::CPL:
        opcode.dst_l->set(opcode.dst_l->get() ^ 0xFF);
        F.N = true;
        F.H = true;
        break;
    case Opcode::CCF:
        F.N = false;
        F.H = false;
        F.C = !F.C;
        break;

    case Opcode::ADD8TO16:{
        int dst = opcode.dst_l->get() | opcode.dst_h->get() << 8;
        int src = int8_t(opcode.src_l->get());
        int res = dst + src;
        int tmp = dst ^ src ^ res;
        F.Z = false;
        F.H = tmp & 0x10;
        F.N = false;
        F.C = tmp & 0x100;
        opcode.dst_l->set(res);
        opcode.dst_h->set(res >> 8);
        }break;
    case Opcode::LDSPADD8:{
        int dst = getSP();
        int src = int8_t(opcode.src_l->get());
        int res = dst + src;
        int tmp = dst ^ src ^ res;
        F.Z = false;
        F.H = tmp & 0x10;
        F.N = false;
        F.C = tmp & 0x100;
        opcode.dst_l->set(res);
        opcode.dst_h->set(res >> 8);
        }break;
    case Opcode::RST:
        mm::get(getSP() - 1).set(pc >> 8);
        mm::get(getSP() - 2).set(pc);
        setSP(getSP() - 2);
        pc = opcode.value;
        break;

    case Opcode::RLC:
        tmp = opcode.dst_l->get();
        opcode.dst_l->set((tmp << 1) | (tmp >> 7));
        F.Z = opcode.dst_l->get() == 0x00;
        F.N = false;
        F.H = false;
        F.C = tmp & 0x80;
        break;
    case Opcode::RRC:
        tmp = opcode.dst_l->get();
        opcode.dst_l->set((tmp >> 1) | (tmp << 7));
        F.Z = opcode.dst_l->get() == 0x00;
        F.N = false;
        F.H = false;
        F.C = tmp & 0x01;
        break;
    case Opcode::RL:
        tmp = opcode.dst_l->get();
        if (F.C)
            opcode.dst_l->set((tmp << 1) | 0x01);
        else
            opcode.dst_l->set((tmp << 1));
        F.Z = opcode.dst_l->get() == 0x00;
        F.N = false;
        F.H = false;
        F.C = tmp & 0x80;
        break;
    case Opcode::RR:
        tmp = opcode.dst_l->get();
        if (F.C)
            opcode.dst_l->set((tmp >> 1) | 0x80);
        else
            opcode.dst_l->set((tmp >> 1));
        F.Z = opcode.dst_l->get() == 0x00;
        F.N = false;
        F.H = false;
        F.C = tmp & 0x01;
        break;
    case Opcode::SLA:
        tmp = opcode.dst_l->get();
        opcode.dst_l->set(tmp << 1);
        F.Z = opcode.dst_l->get() == 0x00;
        F.N = false;
        F.H = false;
        F.C = tmp & 0x80;
        break;
    case Opcode::SRA:
        tmp = opcode.dst_l->get();
        opcode.dst_l->set(tmp >> 1 | (tmp & 0x80));
        F.Z = opcode.dst_l->get() == 0x00;
        F.N = false;
        F.H = false;
        F.C = tmp & 0x01;
        break;
    case Opcode::SWAP:
        tmp = opcode.dst_l->get();
        opcode.dst_l->set((tmp >> 4) | (tmp << 4));
        F.Z = tmp == 0x00;
        F.N = F.H = F.C = false;
        break;
    case Opcode::SRL:
        tmp = opcode.dst_l->get();
        F.C = tmp & 0x01;
        tmp >>= 1;
        opcode.dst_l->set(tmp);
        F.H = F.N = false;
        F.Z = tmp == 0x00;
        break;

    case Opcode::BIT:
        F.Z = (opcode.dst_l->get() & (1 << opcode.value)) == 0x00;
        F.N = false;
        F.H = true;
        break;
    case Opcode::RES:
        opcode.dst_l->set(opcode.dst_l->get() & ~(1 << opcode.value));
        break;
    case Opcode::SET:
        opcode.dst_l->set(opcode.dst_l->get() | (1 << opcode.value));
        break;

    case Opcode::ERROR: NOT_IMPLEMENTED(); break;
    }
}

void Cpu::setInterrupt(uint8_t mask)
{
    cpu.IF.value |= mask;
    if (cpu.IE.value & mask)
        cpu.halt = false;
}

void Cpu::interrupt(uint16_t vector)
{
    ime = false;
    mm::get(getSP() - 1).set(pc >> 8);
    mm::get(getSP() - 2).set(pc);
    setSP(getSP() - 2);
    pc = vector;
}
