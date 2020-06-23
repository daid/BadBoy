import struct

NOP = "nop"
STOP = "stop"
HALT = "halt"
JP = "jp"
JR = "jr"
LD = "ld"
LDH = "ldh"
ADD = "add"
ADC = "adc"
SUB = "sub"
SBC = "sbc"
AND = "and"
OR = "or"
XOR = "xor"
CP = "cp"
RST = "rst"
RET = "ret"
RETI = "reti"
CALL = "call"
INC = "inc"
DEC = "dec"
PUSH = "push"
POP = "pop"
EI = "ei"
DI = "di"
RLCA = "rlca"
RLA = "rla"
DAA = "daa"
SCF = "scf"
RRCA = "rrca"
RRA = "rra"
CPL = "cpl"
CCF = "ccf"

RLC = "rlc"
RRC = "rrc"
RL = "rl"
RR = "rr"
SLA = "sla"
SRA = "sra"
SWAP = "swap"
SRL = "srl"
BIT = "bit"
RES = "res"
SET = "set"

COND_Z = "Z"
COND_NZ = "NZ"
COND_C = "C"
COND_NC = "NC"

AF = "AF"
BC = "BC"
DE = "DE"
HL = "HL"
SP = "SP"
A = "A"
B = "B"
C = "C"
D = "D"
E = "E"
H = "H"
L = "L"


class Ref:
    def __init__(self, target):
        self.target = target

    def __repr__(self):
        return "[%s]" % (self.target)


class Word:
    def __init__(self, target):
        self.target = target

    def __repr__(self):
        return "$%04x" % (self.target)


class Instruction:
    def __init__(self, rom, address):
        self.rom = rom
        self.address = address
        self.type = None
        self.condition = None
        self.p0 = None
        self.p1 = None
        self.size = 1

        op = rom.data[address]

        if op == 0x00: self.__set(NOP)
        if op == 0x10: self.__set(STOP)
        if op == 0x20: self.__set(JR, self.__getRelativeWord(), condition=COND_NZ)
        if op == 0x30: self.__set(JR, self.__getRelativeWord(), condition=COND_NC)

        if op == 0x01: self.__set(LD, BC, self.__getUInt16())
        if op == 0x11: self.__set(LD, DE, self.__getUInt16())
        if op == 0x21: self.__set(LD, HL, self.__getUInt16())
        if op == 0x31: self.__set(LD, SP, self.__getUInt16())

        if op == 0x02: self.__set(LD, Ref(BC), A)
        if op == 0x12: self.__set(LD, Ref(DE), A)
        if op == 0x22: self.__set(LD, Ref("HL+"), A)
        if op == 0x32: self.__set(LD, Ref("HL-"), A)

        if op == 0x03: self.__set(INC, BC)
        if op == 0x13: self.__set(INC, DE)
        if op == 0x23: self.__set(INC, HL)
        if op == 0x33: self.__set(INC, SP)

        if op == 0x04: self.__set(INC, B)
        if op == 0x14: self.__set(INC, D)
        if op == 0x24: self.__set(INC, H)
        if op == 0x34: self.__set(INC, Ref(HL))

        if op == 0x05: self.__set(DEC, B)
        if op == 0x15: self.__set(DEC, D)
        if op == 0x25: self.__set(DEC, H)
        if op == 0x35: self.__set(DEC, Ref(HL))

        if op == 0x06: self.__set(LD, B, self.__getUInt8())
        if op == 0x16: self.__set(LD, D, self.__getUInt8())
        if op == 0x26: self.__set(LD, H, self.__getUInt8())
        if op == 0x36: self.__set(LD, Ref(HL), self.__getUInt8())

        if op == 0x07: self.__set(RLCA)
        if op == 0x17: self.__set(RLA)
        if op == 0x27: self.__set(DAA)
        if op == 0x37: self.__set(SCF)

        if op == 0x08: self.__set(LD, Ref(self.__getUInt16()), SP)
        if op == 0x18: self.__set(JR, self.__getRelativeWord())
        if op == 0x28: self.__set(JR, self.__getRelativeWord(), condition=COND_Z)
        if op == 0x38: self.__set(JR, self.__getRelativeWord(), condition=COND_C)

        if op == 0x09: self.__set(ADD, HL, BC)
        if op == 0x19: self.__set(ADD, HL, DE)
        if op == 0x29: self.__set(ADD, HL, HL)
        if op == 0x39: self.__set(ADD, HL, SP)

        if op == 0x0A: self.__set(LD, A, Ref(BC))
        if op == 0x1A: self.__set(LD, A, Ref(DE))
        if op == 0x2A: self.__set(LD, A, Ref("HL+"))
        if op == 0x3A: self.__set(LD, A, Ref("HL-"))

        if op == 0x0B: self.__set(DEC, BC)
        if op == 0x1B: self.__set(DEC, DE)
        if op == 0x2B: self.__set(DEC, HL)
        if op == 0x3B: self.__set(DEC, SP)

        if op == 0x0C: self.__set(INC, C)
        if op == 0x1C: self.__set(INC, E)
        if op == 0x2C: self.__set(INC, L)
        if op == 0x3C: self.__set(INC, A)

        if op == 0x0D: self.__set(DEC, C)
        if op == 0x1D: self.__set(DEC, E)
        if op == 0x2D: self.__set(DEC, L)
        if op == 0x3D: self.__set(DEC, A)

        if op == 0x0E: self.__set(LD, C, self.__getUInt8())
        if op == 0x1E: self.__set(LD, E, self.__getUInt8())
        if op == 0x2E: self.__set(LD, L, self.__getUInt8())
        if op == 0x3E: self.__set(LD, A, self.__getUInt8())

        if op == 0x0F: self.__set(RRCA)
        if op == 0x1F: self.__set(RRA)
        if op == 0x2F: self.__set(CPL)
        if op == 0x3F: self.__set(CCF)

        if op == 0x40: self.__set(LD, B, B)
        if op == 0x50: self.__set(LD, D, B)
        if op == 0x60: self.__set(LD, H, B)
        if op == 0x70: self.__set(LD, Ref(HL), B)

        if op == 0x41: self.__set(LD, B, C)
        if op == 0x51: self.__set(LD, D, C)
        if op == 0x61: self.__set(LD, H, C)
        if op == 0x71: self.__set(LD, Ref(HL), C)

        if op == 0x42: self.__set(LD, B, D)
        if op == 0x52: self.__set(LD, D, D)
        if op == 0x62: self.__set(LD, H, D)
        if op == 0x72: self.__set(LD, Ref(HL), D)

        if op == 0x43: self.__set(LD, B, E)
        if op == 0x53: self.__set(LD, D, E)
        if op == 0x63: self.__set(LD, H, E)
        if op == 0x73: self.__set(LD, Ref(HL), E)

        if op == 0x44: self.__set(LD, B, H)
        if op == 0x54: self.__set(LD, D, H)
        if op == 0x64: self.__set(LD, H, H)
        if op == 0x74: self.__set(LD, Ref(HL), H)

        if op == 0x45: self.__set(LD, B, L)
        if op == 0x55: self.__set(LD, D, L)
        if op == 0x65: self.__set(LD, H, L)
        if op == 0x75: self.__set(LD, Ref(HL), L)

        if op == 0x46: self.__set(LD, B, Ref(HL))
        if op == 0x56: self.__set(LD, D, Ref(HL))
        if op == 0x66: self.__set(LD, H, Ref(HL))
        if op == 0x76:
            assert self.__getUInt8() == 0x00 # Needs a NOP after HALT
            self.__set(HALT)

        if op == 0x47: self.__set(LD, B, A)
        if op == 0x57: self.__set(LD, D, A)
        if op == 0x67: self.__set(LD, H, A)
        if op == 0x77: self.__set(LD, Ref(HL), A)

        if op == 0x48: self.__set(LD, C, B)
        if op == 0x58: self.__set(LD, E, B)
        if op == 0x68: self.__set(LD, L, B)
        if op == 0x78: self.__set(LD, A, B)

        if op == 0x49: self.__set(LD, C, C)
        if op == 0x59: self.__set(LD, E, C)
        if op == 0x69: self.__set(LD, L, C)
        if op == 0x79: self.__set(LD, A, C)

        if op == 0x4A: self.__set(LD, C, D)
        if op == 0x5A: self.__set(LD, E, D)
        if op == 0x6A: self.__set(LD, L, D)
        if op == 0x7A: self.__set(LD, A, D)

        if op == 0x4B: self.__set(LD, C, E)
        if op == 0x5B: self.__set(LD, E, E)
        if op == 0x6B: self.__set(LD, L, E)
        if op == 0x7B: self.__set(LD, A, E)

        if op == 0x4C: self.__set(LD, C, H)
        if op == 0x5C: self.__set(LD, E, H)
        if op == 0x6C: self.__set(LD, L, H)
        if op == 0x7C: self.__set(LD, A, H)

        if op == 0x4D: self.__set(LD, C, L)
        if op == 0x5D: self.__set(LD, E, L)
        if op == 0x6D: self.__set(LD, L, L)
        if op == 0x7D: self.__set(LD, A, L)

        if op == 0x4E: self.__set(LD, C, Ref(HL))
        if op == 0x5E: self.__set(LD, E, Ref(HL))
        if op == 0x6E: self.__set(LD, L, Ref(HL))
        if op == 0x7E: self.__set(LD, A, Ref(HL))

        if op == 0x4F: self.__set(LD, C, A)
        if op == 0x5F: self.__set(LD, E, A)
        if op == 0x6F: self.__set(LD, L, A)
        if op == 0x7F: self.__set(LD, A, A)

        if op == 0x80: self.__set(ADD, A, B)
        if op == 0x81: self.__set(ADD, A, C)
        if op == 0x82: self.__set(ADD, A, D)
        if op == 0x83: self.__set(ADD, A, E)
        if op == 0x84: self.__set(ADD, A, H)
        if op == 0x85: self.__set(ADD, A, L)
        if op == 0x86: self.__set(ADD, A, Ref(HL))
        if op == 0x87: self.__set(ADD, A, A)

        if op == 0x88: self.__set(ADC, A, B)
        if op == 0x89: self.__set(ADC, A, C)
        if op == 0x8A: self.__set(ADC, A, D)
        if op == 0x8B: self.__set(ADC, A, E)
        if op == 0x8C: self.__set(ADC, A, H)
        if op == 0x8D: self.__set(ADC, A, L)
        if op == 0x8E: self.__set(ADC, A, Ref(HL))
        if op == 0x8F: self.__set(ADC, A, A)

        if op == 0x90: self.__set(SUB, A, B)
        if op == 0x91: self.__set(SUB, A, C)
        if op == 0x92: self.__set(SUB, A, D)
        if op == 0x93: self.__set(SUB, A, E)
        if op == 0x94: self.__set(SUB, A, H)
        if op == 0x95: self.__set(SUB, A, L)
        if op == 0x96: self.__set(SUB, A, Ref(HL))
        if op == 0x97: self.__set(SUB, A, A)

        if op == 0x98: self.__set(SBC, A, B)
        if op == 0x99: self.__set(SBC, A, C)
        if op == 0x9A: self.__set(SBC, A, D)
        if op == 0x9B: self.__set(SBC, A, E)
        if op == 0x9C: self.__set(SBC, A, H)
        if op == 0x9D: self.__set(SBC, A, L)
        if op == 0x9E: self.__set(SBC, A, Ref(HL))
        if op == 0x9F: self.__set(SBC, A, A)

        if op == 0xA0: self.__set(AND, A, B)
        if op == 0xA1: self.__set(AND, A, C)
        if op == 0xA2: self.__set(AND, A, D)
        if op == 0xA3: self.__set(AND, A, E)
        if op == 0xA4: self.__set(AND, A, H)
        if op == 0xA5: self.__set(AND, A, L)
        if op == 0xA6: self.__set(AND, A, Ref(HL))
        if op == 0xA7: self.__set(AND, A, A)

        if op == 0xA8: self.__set(XOR, A, B)
        if op == 0xA9: self.__set(XOR, A, C)
        if op == 0xAA: self.__set(XOR, A, D)
        if op == 0xAB: self.__set(XOR, A, E)
        if op == 0xAC: self.__set(XOR, A, H)
        if op == 0xAD: self.__set(XOR, A, L)
        if op == 0xAE: self.__set(XOR, A, Ref(HL))
        if op == 0xAF: self.__set(XOR, A, A)

        if op == 0xB0: self.__set(OR, A, B)
        if op == 0xB1: self.__set(OR, A, C)
        if op == 0xB2: self.__set(OR, A, D)
        if op == 0xB3: self.__set(OR, A, E)
        if op == 0xB4: self.__set(OR, A, H)
        if op == 0xB5: self.__set(OR, A, L)
        if op == 0xB6: self.__set(OR, A, Ref(HL))
        if op == 0xB7: self.__set(OR, A, A)

        if op == 0xB8: self.__set(CP, A, B)
        if op == 0xB9: self.__set(CP, A, C)
        if op == 0xBA: self.__set(CP, A, D)
        if op == 0xBB: self.__set(CP, A, E)
        if op == 0xBC: self.__set(CP, A, H)
        if op == 0xBD: self.__set(CP, A, L)
        if op == 0xBE: self.__set(CP, A, Ref(HL))
        if op == 0xBF: self.__set(CP, A, A)

        if op == 0xC0: self.__set(RET, condition=COND_NZ)
        if op == 0xD0: self.__set(RET, condition=COND_NC)
        if op == 0xE0: self.__set(LDH, Ref(0xFF00 | self.__getUInt8()), A)
        if op == 0xF0: self.__set(LDH, A, Ref(0xFF00 | self.__getUInt8()))

        if op == 0xC1: self.__set(POP, BC)
        if op == 0xD1: self.__set(POP, DE)
        if op == 0xE1: self.__set(POP, HL)
        if op == 0xF1: self.__set(POP, AF)

        if op == 0xC2: self.__set(JP, self.__getUInt16(), condition=COND_NZ)
        if op == 0xD2: self.__set(JP, self.__getUInt16(), condition=COND_NC)
        if op == 0xE2: self.__set(LDH, Ref(C), A)
        if op == 0xF2: self.__set(LDH, A, Ref(C))

        if op == 0xC3: self.__set(JP, self.__getUInt16())
        # if op == 0xD3: self.__set(ERROR)
        # if op == 0xE3: self.__set(ERROR)
        if op == 0xF3: self.__set(DI)

        if op == 0xC4: self.__set(CALL, self.__getUInt16(), condition=COND_NZ)
        if op == 0xD4: self.__set(CALL, self.__getUInt16(), condition=COND_NC)
        # if op == 0xE4: self.__set(ERROR)
        # if op == 0xF4: self.__set(ERROR)

        if op == 0xC5: self.__set(PUSH, BC)
        if op == 0xD5: self.__set(PUSH, DE)
        if op == 0xE5: self.__set(PUSH, HL)
        if op == 0xF5: self.__set(PUSH, AF)

        if op == 0xC6: self.__set(ADD, A, self.__getUInt8())
        if op == 0xD6: self.__set(SUB, A, self.__getUInt8())
        if op == 0xE6: self.__set(AND, A, self.__getUInt8())
        if op == 0xF6: self.__set(OR, A, self.__getUInt8())

        if op == 0xC7: self.__set(RST, 0x0000)
        if op == 0xD7: self.__set(RST, 0x0010)
        if op == 0xE7: self.__set(RST, 0x0020)
        if op == 0xF7: self.__set(RST, 0x0030)

        if op == 0xC8: self.__set(RET, condition=COND_Z)
        if op == 0xD8: self.__set(RET, condition=COND_C)
        if op == 0xE8: self.__set(ADD, SP, self.__getInt8())
        if op == 0xF8: self.__set(LD, HL, "SP%+d" % (self.__getInt8()))

        if op == 0xC9: self.__set(RET)
        if op == 0xD9: self.__set(RETI)
        if op == 0xE9: self.__set(JP, HL)
        if op == 0xF9: self.__set(LD, SP, HL)

        if op == 0xCA: self.__set(JP, self.__getUInt16(), condition=COND_Z)
        if op == 0xDA: self.__set(JP, self.__getUInt16(), condition=COND_C)
        if op == 0xEA: self.__set(LD, Ref(self.__getUInt16()), A)
        if op == 0xFA: self.__set(LD, A, Ref(self.__getUInt16()))

        if op == 0xCB: self.__decodeCB(self.__getUInt8())
        # if op == 0xDB: self.__set(ERROR)
        # if op == 0xEB: self.__set(ERROR)
        if op == 0xFB: self.__set(EI)

        if op == 0xCC: self.__set(CALL, self.__getUInt16(), condition=COND_Z)
        if op == 0xDC: self.__set(CALL, self.__getUInt16(), condition=COND_C)
        # if op == 0xEC: self.__set(ERROR)
        # if op == 0xFC: self.__set(ERROR)

        if op == 0xCD: self.__set(CALL, self.__getUInt16())
        # if op == 0xDD: self.__set(ERROR)
        # if op == 0xED: self.__set(ERROR)
        # if op == 0xFD: self.__set(ERROR)

        if op == 0xCE: self.__set(ADC, A, self.__getUInt8())
        if op == 0xDE: self.__set(SBC, A, self.__getUInt8())
        if op == 0xEE: self.__set(XOR, A, self.__getUInt8())
        if op == 0xFE: self.__set(CP, A, self.__getUInt8())

        if op == 0xCF: self.__set(RST, 0x0008)
        if op == 0xDF: self.__set(RST, 0x0018)
        if op == 0xEF: self.__set(RST, 0x0028)
        if op == 0xFF: self.__set(RST, 0x0038)

        assert self.type is not None, "Decode failed for: %04X:%02X" % (address, op)

    def __decodeCB(self, op):
        if (op & 0x07) == 0: self.p0 = B
        if (op & 0x07) == 1: self.p0 = C
        if (op & 0x07) == 2: self.p0 = D
        if (op & 0x07) == 3: self.p0 = E
        if (op & 0x07) == 4: self.p0 = H
        if (op & 0x07) == 5: self.p0 = L
        if (op & 0x07) == 6: self.p0 = Ref(HL)
        if (op & 0x07) == 7: self.p0 = A
        if op < 0x40:
            if (op & 0xF8) == 0x00: self.type = RLC
            if (op & 0xF8) == 0x08: self.type = RRC
            if (op & 0xF8) == 0x10: self.type = RL
            if (op & 0xF8) == 0x18: self.type = RR
            if (op & 0xF8) == 0x20: self.type = SLA
            if (op & 0xF8) == 0x28: self.type = SRA
            if (op & 0xF8) == 0x30: self.type = SWAP
            if (op & 0xF8) == 0x38: self.type = SRL
        else:
            self.p1 = self.p0
            self.p0 = (op >> 3) & 0x07
            if (op & 0xC0) == 0x40: self.type = BIT
            if (op & 0xC0) == 0x80: self.type = RES
            if (op & 0xC0) == 0xC0: self.type = SET

    def __set(self, instr_type, p0=None, p1=None, *, condition=None):
        self.type = instr_type
        self.condition = condition
        self.p0 = p0
        self.p1 = p1

    def __getInt8(self):
        self.size += 1
        return struct.unpack("b", self.rom.data[self.address+self.size-1:self.address + self.size])[0]

    def __getRelativeWord(self):
        address = self.address+2+self.__getInt8()
        if address > 0x4000:
            address = (address & 0x3FFF) | 0x4000
        return Word(address)

    def __getUInt8(self):
        self.size += 1
        return struct.unpack("B", self.rom.data[self.address+self.size-1:self.address + self.size])[0]

    def __getUInt16(self):
        self.size += 2
        return Word(struct.unpack("<H", self.rom.data[self.address + self.size - 2:self.address + self.size])[0])

    def hasNext(self):
        if self.type in (JP, JR, RET) and self.condition is None:
            return False
        if self.type == RETI:
            return False
        return True

    def jumpTarget(self):
        if self.type in (CALL, JP, JR) and self.p0 != HL:
            if isinstance(self.p0, Word):
                return self.p0.target
            return self.p0
        return None

    def format(self, info):
        p0, p1 = self.p0, self.p1

        if self.type == LD and isinstance(self.p0, Ref) and isinstance(self.p0.target, Word) and self.p0.target.target >= 0xFF00 and self.p1 == A:
            return "ld_long_store %s" % (info.formatParameter(self.address, p0.target))
        if self.type == LD and isinstance(self.p1, Ref) and isinstance(self.p1.target, Word) and self.p1.target.target >= 0xFF00 and self.p0 == A:
            return "ld_long_load %s" % (info.formatParameter(self.address, p1.target))

        if self.condition is not None:
            p1 = p0
            p0 = self.condition
        if p0 is None:
            return "%s" % (self.type)
        if p1 is None:
            return "%-4s %s" % (self.type, info.formatParameter(self.address, p0, pc_target=self.type in (CALL, JR, JP, RST)))
        return "%-4s %s, %s" % (self.type, info.formatParameter(self.address, p0), info.formatParameter(self.address, p1))

    def __repr__(self):
        return "%s %s %s %s" % (self.type, self.condition, self.p0, self.p1)
