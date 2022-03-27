#include <stdio.h>
#include <unistd.h>

#include "cpu.h"
#include "mm.h"
#include "card.h"
#include "video.h"
#include "ram.h"
#include "audio.h"

Cpu cpu;

void Cpu::reset()
{
    card.init();
    video.init();
    ram.init();
    audio.init();

    for(uint32_t n=0xFF00; n<0xFF80; n++)
        mm::get(n).id = n | ID_IO;
    mm::get(0xFF7F).id = std::numeric_limits<uint64_t>::max();
    mm::get(0xFFFF).id = 0xFFFF | ID_IO;

    gbc = card.getRom(0x143).get() & 0x80;
    if (card.getBoot(0).get() == 0x00)
    {
        //Skip the bootrom and setup the defaults as they would be after the bootrom.
        A.set(gbc ? 0x11 : 0x01);
        F.set(0xB0);
        B.set(0x00);
        C.set(0x13);
        D.set(0x00);
        E.set(0xD8);
        H.set(0x01);
        L.set(0x4D);
        S.set(0xFF);
        P.set(0xFE);
        video.LCDC.set(0x91);
        video.BGP.set(0xFC);
        video.OBP0.set(0xFF);
        video.OBP1.set(0xFF);
        audio.NR10.set(0x80);
        audio.NR11.set(0xBF);
        audio.NR12.set(0xF3);
        audio.NR14.set(0xBF);
        audio.NR21.set(0x3F);
        audio.NR22.set(0x00);
        audio.NR24.set(0xBF);
        audio.NR30.set(0x7F);
        audio.NR31.set(0xFF);
        audio.NR32.set(0x9F);
        audio.NR43.set(0xBF);
        audio.NR41.set(0xFF);
        audio.NR42.set(0x00);
        audio.NR43.set(0x00);
        audio.NR44.set(0xBF);
        audio.NR50.set(0x77);
        audio.NR51.set(0xF3);
        audio.NR52.set(0xF1);
        audio.square_1.active = false;
        mm::get(0xFF50).set(0x01);
        pc = 0x100;
    }
}

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

void Cpu::execute(const Opcode& opcode)
{
    mm::get(pc).mark(MARK_INSTR);
    for(uint16_t n=pc+1; n<pc+opcode.size; n++)
        mm::get(n).mark(MARK_INSTR | MARK_DATA);
    uint8_t tmp;
    pc += opcode.size;
    cycles += opcode.cycles;
    switch(opcode.type)
    {
    case Opcode::NOP: break;
    case Opcode::STOP:
        if (cpu.gbc && (cpu.KEY1.get() & 0x01))
        {
            //TODO: This should take 0x2000 cycles according to tests.
            cpu.speed = (cpu.speed == 1) ? 2 : 1;
            cpu.KEY1.set(cpu.speed == 1 ? 0x00 : 0x80);
        } else {
            //TODO: Put the system in stopped mode, not emulated yet due to limited use.
        }
        break;
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
        opcode.dst_l->markOrigin(MARK_WORD_LOW);
        opcode.dst_h->markOrigin(MARK_WORD_HIGH);
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
        if (tmp != opcode.dst_l->get()) // prevent breaking origin tracking if nothing is added
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
        if (tmp != opcode.dst_l->get()) // prevent breaking origin tracking if nothing is added
            opcode.dst_l->set(tmp);
        break;
    case Opcode::ADD16:{
        opcode.src_l->markOrigin(MARK_WORD_LOW);
        opcode.src_h->markOrigin(MARK_WORD_HIGH);
        opcode.dst_l->markOrigin(MARK_WORD_LOW);
        opcode.dst_h->markOrigin(MARK_WORD_HIGH);
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
        if (opcode.dst_l != opcode.src_l) // prevent breaking origin checking on "and A", which is often used to check for zero.
            opcode.dst_l->set(opcode.dst_l->get() & opcode.src_l->get());
        F.Z = opcode.dst_l->get() == 0x00;
        F.N = false;
        F.H = true;
        F.C = false;
        break;
    case Opcode::XOR8:
        if (opcode.src_l->get() != 0x00) // prevent breaking origin checking on flipping sprite attributes
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
        opcode.dst_l->markOrigin(MARK_PTR_LOW);
        opcode.dst_h->markOrigin(MARK_PTR_HIGH);
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
        mm::get(getSP() - 1).set(*opcode.dst_h);
        mm::get(getSP() - 2).set(*opcode.dst_l);
        setSP(getSP() - 2);
        break;
    case Opcode::POP16:
        opcode.dst_l->set(mm::get(getSP()));
        opcode.dst_h->set(mm::get(getSP() + 1));
        setSP(getSP() + 2);
        break;

    case Opcode::RET:
        mm::get(getSP()).markOrigin(MARK_PTR_LOW);
        mm::get(getSP()+1).markOrigin(MARK_PTR_HIGH);
        pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
        setSP(getSP() + 2);
        break;
    case Opcode::RETZ:
        if (F.Z)
        {
            mm::get(getSP()).markOrigin(MARK_PTR_LOW);
            mm::get(getSP()+1).markOrigin(MARK_PTR_HIGH);
            pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
            setSP(getSP() + 2);
            cycles += 12;
        }
        break;
    case Opcode::RETC:
        if (F.C)
        {
            mm::get(getSP()).markOrigin(MARK_PTR_LOW);
            mm::get(getSP()+1).markOrigin(MARK_PTR_HIGH);
            pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
            setSP(getSP() + 2);
            cycles += 12;
        }
        break;
    case Opcode::RETNZ:
        if (!F.Z)
        {
            mm::get(getSP()).markOrigin(MARK_PTR_LOW);
            mm::get(getSP()+1).markOrigin(MARK_PTR_HIGH);
            pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
            setSP(getSP() + 2);
            cycles += 12;
        }
        break;
    case Opcode::RETNC:
        if (!F.C)
        {
            mm::get(getSP()).markOrigin(MARK_PTR_LOW);
            mm::get(getSP()+1).markOrigin(MARK_PTR_HIGH);
            pc = mm::get(getSP()).get() | (mm::get(getSP()+1).get() << 8);
            setSP(getSP() + 2);
            cycles += 12;
        }
        break;
    case Opcode::RETI:
        mm::get(getSP()).markOrigin(MARK_PTR_LOW);
        mm::get(getSP()+1).markOrigin(MARK_PTR_HIGH);
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

    case Opcode::ERROR:
        break;
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
    cycles += 20;
    ime = false;
    mm::get(getSP() - 1).set(pc >> 8);
    mm::get(getSP() - 2).set(pc);
    setSP(getSP() - 2);
    pc = vector;
}
