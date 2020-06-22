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

COND_Z = "z"
COND_NZ = "nz"
COND_C = "c"
COND_NC = "nc"

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


class Instruction:
    def __init__(self, rom, address):
        self.rom = rom
        self.address = address
        self.type = None
        self.condition = None
        self.target = None
        self.source = None
        self.value = None
        self.size = 1

        op = rom.data[address]

        if op == 0x00: self.__set(NOP)
        if op == 0x10: self.__set(STOP)
        if op == 0x20: self.__set(JR, condition=COND_NZ, target=address+2+self.__getInt8())
        if op == 0x30: self.__set(JR, condition=COND_NC, target=address+2+self.__getInt8())

        if op == 0x01: self.__set(LD, target=BC, value=self.__getUInt16())
        if op == 0x11: self.__set(LD, target=DE, value=self.__getUInt16())
        if op == 0x21: self.__set(LD, target=HL, value=self.__getUInt16())
        if op == 0x31: self.__set(LD, target=SP, value=self.__getUInt16())

        if op == 0x02: self.__set(LD, target=[BC], source=A)
        if op == 0x12: self.__set(LD, target=[DE], source=A)
        if op == 0x22: self.__set(LD, target=["HL+"], source=A)
        if op == 0x32: self.__set(LD, target=["HL-"], source=A)

        if op == 0x03: self.__set(INC, target=BC)
        if op == 0x13: self.__set(INC, target=DE)
        if op == 0x23: self.__set(INC, target=HL)
        if op == 0x33: self.__set(INC, target=SP)

        if op == 0x04: self.__set(INC, target=B)
        if op == 0x14: self.__set(INC, target=D)
        if op == 0x24: self.__set(INC, target=H)
        if op == 0x34: self.__set(INC, target=[HL])

        if op == 0x05: self.__set(DEC, target=B)
        if op == 0x15: self.__set(DEC, target=D)
        if op == 0x25: self.__set(DEC, target=H)
        if op == 0x35: self.__set(DEC, target=[HL])

        if op == 0x06: self.__set(LD, target=B, value=self.__getUInt8())
        if op == 0x16: self.__set(LD, target=D, value=self.__getUInt8())
        if op == 0x26: self.__set(LD, target=H, value=self.__getUInt8())
        if op == 0x36: self.__set(LD, target=[HL], value=self.__getUInt8())

        if op == 0x07: self.__set(RLCA)
        if op == 0x17: self.__set(RLA)
        if op == 0x27: self.__set(DAA)
        if op == 0x37: self.__set(SCF)

        if op == 0x08: self.__set(LD, target=[self.__getUInt16()], source=SP)
        if op == 0x18: self.__set(JR, target=address+2+self.__getInt8())
        if op == 0x28: self.__set(JR, condition=COND_Z, target=address+2+self.__getInt8())
        if op == 0x38: self.__set(JR, condition=COND_C, target=address+2+self.__getInt8())

        if op == 0x09: self.__set(ADD, target=HL, source=BC)
        if op == 0x19: self.__set(ADD, target=HL, source=DE)
        if op == 0x29: self.__set(ADD, target=HL, source=HL)
        if op == 0x39: self.__set(ADD, target=HL, source=SP)

        if op == 0x0A: self.__set(LD, target=A, source=[BC])
        if op == 0x1A: self.__set(LD, target=A, source=[DE])
        if op == 0x2A: self.__set(LD, target=A, source=["HL+"])
        if op == 0x3A: self.__set(LD, target=A, source=["HL-"])

        if op == 0x0B: self.__set(DEC, target=BC)
        if op == 0x1B: self.__set(DEC, target=DE)
        if op == 0x2B: self.__set(DEC, target=HL)
        if op == 0x3B: self.__set(DEC, target=SP)

        if op == 0x0C: self.__set(INC, target=C)
        if op == 0x1C: self.__set(INC, target=E)
        if op == 0x2C: self.__set(INC, target=L)
        if op == 0x3C: self.__set(INC, target=A)

        if op == 0x0D: self.__set(DEC, target=C)
        if op == 0x1D: self.__set(DEC, target=E)
        if op == 0x2D: self.__set(DEC, target=L)
        if op == 0x3D: self.__set(DEC, target=A)

        if op == 0x0E: self.__set(LD, target=C, value=self.__getUInt8())
        if op == 0x1E: self.__set(LD, target=E, value=self.__getUInt8())
        if op == 0x2E: self.__set(LD, target=L, value=self.__getUInt8())
        if op == 0x3E: self.__set(LD, target=A, value=self.__getUInt8())

        if op == 0x0F: self.__set(RRCA)
        if op == 0x1F: self.__set(RRA)
        if op == 0x2F: self.__set(CPL)
        if op == 0x3F: self.__set(CCF)

        if op == 0x40: self.__set(LD, target=B, source=B)
        if op == 0x50: self.__set(LD, target=D, source=B)
        if op == 0x60: self.__set(LD, target=H, source=B)
        if op == 0x70: self.__set(LD, target=[HL], source=B)

        if op == 0x41: self.__set(LD, target=B, source=C)
        if op == 0x51: self.__set(LD, target=D, source=C)
        if op == 0x61: self.__set(LD, target=H, source=C)
        if op == 0x71: self.__set(LD, target=[HL], source=C)

        if op == 0x42: self.__set(LD, target=B, source=D)
        if op == 0x52: self.__set(LD, target=D, source=D)
        if op == 0x62: self.__set(LD, target=H, source=D)
        if op == 0x72: self.__set(LD, target=[HL], source=D)

        if op == 0x43: self.__set(LD, target=B, source=E)
        if op == 0x53: self.__set(LD, target=D, source=E)
        if op == 0x63: self.__set(LD, target=H, source=E)
        if op == 0x73: self.__set(LD, target=[HL], source=E)

        if op == 0x44: self.__set(LD, target=B, source=H)
        if op == 0x54: self.__set(LD, target=D, source=H)
        if op == 0x64: self.__set(LD, target=H, source=H)
        if op == 0x74: self.__set(LD, target=[HL], source=H)

        if op == 0x45: self.__set(LD, target=B, source=L)
        if op == 0x55: self.__set(LD, target=D, source=L)
        if op == 0x65: self.__set(LD, target=H, source=L)
        if op == 0x75: self.__set(LD, target=[HL], source=L)

        if op == 0x46: self.__set(LD, target=B, source=[HL])
        if op == 0x56: self.__set(LD, target=D, source=[HL])
        if op == 0x66: self.__set(LD, target=H, source=[HL])
        if op == 0x76: self.__set(HALT)

        if op == 0x47: self.__set(LD, target=B, source=A)
        if op == 0x57: self.__set(LD, target=D, source=A)
        if op == 0x67: self.__set(LD, target=H, source=A)
        if op == 0x77: self.__set(LD, target=[HL], source=A)

        if op == 0x48: self.__set(LD, target=C, source=B)
        if op == 0x58: self.__set(LD, target=E, source=B)
        if op == 0x68: self.__set(LD, target=L, source=B)
        if op == 0x78: self.__set(LD, target=A, source=B)

        if op == 0x49: self.__set(LD, target=C, source=C)
        if op == 0x59: self.__set(LD, target=E, source=C)
        if op == 0x69: self.__set(LD, target=L, source=C)
        if op == 0x79: self.__set(LD, target=A, source=C)

        if op == 0x4A: self.__set(LD, target=C, source=D)
        if op == 0x5A: self.__set(LD, target=E, source=D)
        if op == 0x6A: self.__set(LD, target=L, source=D)
        if op == 0x7A: self.__set(LD, target=A, source=D)

        if op == 0x4B: self.__set(LD, target=C, source=E)
        if op == 0x5B: self.__set(LD, target=E, source=E)
        if op == 0x6B: self.__set(LD, target=L, source=E)
        if op == 0x7B: self.__set(LD, target=A, source=E)

        if op == 0x4C: self.__set(LD, target=C, source=H)
        if op == 0x5C: self.__set(LD, target=E, source=H)
        if op == 0x6C: self.__set(LD, target=L, source=H)
        if op == 0x7C: self.__set(LD, target=A, source=H)

        if op == 0x4D: self.__set(LD, target=C, source=L)
        if op == 0x5D: self.__set(LD, target=E, source=L)
        if op == 0x6D: self.__set(LD, target=L, source=L)
        if op == 0x7D: self.__set(LD, target=A, source=L)

        if op == 0x4E: self.__set(LD, target=C, source=[HL])
        if op == 0x5E: self.__set(LD, target=E, source=[HL])
        if op == 0x6E: self.__set(LD, target=L, source=[HL])
        if op == 0x7E: self.__set(LD, target=A, source=[HL])

        if op == 0x4F: self.__set(LD, target=C, source=A)
        if op == 0x5F: self.__set(LD, target=E, source=A)
        if op == 0x6F: self.__set(LD, target=L, source=A)
        if op == 0x7F: self.__set(LD, target=A, source=A)

        if op == 0x80: self.__set(ADD, target=A, source=B)
        if op == 0x81: self.__set(ADD, target=A, source=C)
        if op == 0x82: self.__set(ADD, target=A, source=D)
        if op == 0x83: self.__set(ADD, target=A, source=E)
        if op == 0x84: self.__set(ADD, target=A, source=H)
        if op == 0x85: self.__set(ADD, target=A, source=L)
        if op == 0x86: self.__set(ADD, target=A, source=[HL])
        if op == 0x87: self.__set(ADD, target=A, source=A)

        if op == 0x88: self.__set(ADC, target=A, source=B)
        if op == 0x89: self.__set(ADC, target=A, source=C)
        if op == 0x8A: self.__set(ADC, target=A, source=D)
        if op == 0x8B: self.__set(ADC, target=A, source=E)
        if op == 0x8C: self.__set(ADC, target=A, source=H)
        if op == 0x8D: self.__set(ADC, target=A, source=L)
        if op == 0x8E: self.__set(ADC, target=A, source=[HL])
        if op == 0x8F: self.__set(ADC, target=A, source=A)

        if op == 0x90: self.__set(SUB, target=A, source=B)
        if op == 0x91: self.__set(SUB, target=A, source=C)
        if op == 0x92: self.__set(SUB, target=A, source=D)
        if op == 0x93: self.__set(SUB, target=A, source=E)
        if op == 0x94: self.__set(SUB, target=A, source=H)
        if op == 0x95: self.__set(SUB, target=A, source=L)
        if op == 0x96: self.__set(SUB, target=A, source=[HL])
        if op == 0x97: self.__set(SUB, target=A, source=A)

        if op == 0x98: self.__set(SBC, target=A, source=B)
        if op == 0x99: self.__set(SBC, target=A, source=C)
        if op == 0x9A: self.__set(SBC, target=A, source=D)
        if op == 0x9B: self.__set(SBC, target=A, source=E)
        if op == 0x9C: self.__set(SBC, target=A, source=H)
        if op == 0x9D: self.__set(SBC, target=A, source=L)
        if op == 0x9E: self.__set(SBC, target=A, source=[HL])
        if op == 0x9F: self.__set(SBC, target=A, source=A)

        if op == 0xA0: self.__set(AND, target=A, source=B)
        if op == 0xA1: self.__set(AND, target=A, source=C)
        if op == 0xA2: self.__set(AND, target=A, source=D)
        if op == 0xA3: self.__set(AND, target=A, source=E)
        if op == 0xA4: self.__set(AND, target=A, source=H)
        if op == 0xA5: self.__set(AND, target=A, source=L)
        if op == 0xA6: self.__set(AND, target=A, source=[HL])
        if op == 0xA7: self.__set(AND, target=A, source=A)

        if op == 0xA8: self.__set(XOR, target=A, source=B)
        if op == 0xA9: self.__set(XOR, target=A, source=C)
        if op == 0xAA: self.__set(XOR, target=A, source=D)
        if op == 0xAB: self.__set(XOR, target=A, source=E)
        if op == 0xAC: self.__set(XOR, target=A, source=H)
        if op == 0xAD: self.__set(XOR, target=A, source=L)
        if op == 0xAE: self.__set(XOR, target=A, source=[HL])
        if op == 0xAF: self.__set(XOR, target=A, source=A)

        if op == 0xB0: self.__set(OR, target=A, source=B)
        if op == 0xB1: self.__set(OR, target=A, source=C)
        if op == 0xB2: self.__set(OR, target=A, source=D)
        if op == 0xB3: self.__set(OR, target=A, source=E)
        if op == 0xB4: self.__set(OR, target=A, source=H)
        if op == 0xB5: self.__set(OR, target=A, source=L)
        if op == 0xB6: self.__set(OR, target=A, source=[HL])
        if op == 0xB7: self.__set(OR, target=A, source=A)

        if op == 0xB8: self.__set(CP, target=A, source=B)
        if op == 0xB9: self.__set(CP, target=A, source=C)
        if op == 0xBA: self.__set(CP, target=A, source=D)
        if op == 0xBB: self.__set(CP, target=A, source=E)
        if op == 0xBC: self.__set(CP, target=A, source=H)
        if op == 0xBD: self.__set(CP, target=A, source=L)
        if op == 0xBE: self.__set(CP, target=A, source=[HL])
        if op == 0xBF: self.__set(CP, target=A, source=A)

        if op == 0xC0: self.__set(RET, condition=COND_NZ)
        if op == 0xD0: self.__set(RET, condition=COND_NC)
        if op == 0xE0: self.__set(LDH, target=self.__getUInt8(), source=A)
        if op == 0xF0: self.__set(LDH, target=A, source=self.__getUInt8())

        if op == 0xC1: self.__set(POP, target=BC)
        if op == 0xD1: self.__set(POP, target=DE)
        if op == 0xE1: self.__set(POP, target=HL)
        if op == 0xF1: self.__set(POP, target=AF)

        if op == 0xC2: self.__set(JP, condition=COND_NZ, target=self.__getUInt16())
        if op == 0xD2: self.__set(JP, condition=COND_NC, target=self.__getUInt16())
        if op == 0xE2: self.__set(LDH, target=[C], source=A)
        if op == 0xF2: self.__set(LDH, target=A, source=[C])

        if op == 0xC3: self.__set(JP, target=self.__getUInt16())
        # if op == 0xD3: self.__set(ERROR)
        # if op == 0xE3: self.__set(ERROR)
        if op == 0xF3: self.__set(DI)

        if op == 0xC4: self.__set(CALL, condition=COND_NZ, target=self.__getUInt16())
        if op == 0xD4: self.__set(CALL, condition=COND_NC, target=self.__getUInt16())
        # if op == 0xE4: self.__set(ERROR)
        # if op == 0xF4: self.__set(ERROR)

        if op == 0xC5: self.__set(PUSH, target=BC)
        if op == 0xD5: self.__set(PUSH, target=DE)
        if op == 0xE5: self.__set(PUSH, target=HL)
        if op == 0xF5: self.__set(PUSH, target=AF)

        if op == 0xC6: self.__set(ADD, target=A, value=self.__getUInt8())
        if op == 0xD6: self.__set(SUB, target=A, value=self.__getUInt8())
        if op == 0xE6: self.__set(AND, target=A, value=self.__getUInt8())
        if op == 0xF6: self.__set(OR, target=A, value=self.__getUInt8())

        if op == 0xC7: self.__set(RST, value=0x00)
        if op == 0xD7: self.__set(RST, value=0x10)
        if op == 0xE7: self.__set(RST, value=0x20)
        if op == 0xF7: self.__set(RST, value=0x30)

        if op == 0xC8: self.__set(RET, condition=COND_Z)
        if op == 0xD8: self.__set(RET, condition=COND_C)
        # if op == 0xE8: self.__set(ADD8TO16, 2, 16, & cpu.S, & cpu.P, nullptr, & mm::get(address + 1))
        if op == 0xF8: self.__set(LD, target=HL, source="SP%+d" % (self.__getInt8()))

        if op == 0xC9: self.__set(RET)
        if op == 0xD9: self.__set(RETI)
        if op == 0xE9: self.__set(JP, target=HL)
        if op == 0xF9: self.__set(LD, target=SP, source=HL)

        if op == 0xCA: self.__set(JP, condition=COND_Z, target=self.__getUInt16())
        if op == 0xDA: self.__set(JP, condition=COND_C, target=self.__getUInt16())
        if op == 0xEA: self.__set(LD, target=[self.__getUInt16()], source=A)
        if op == 0xFA: self.__set(LD, target=A, source=[self.__getUInt16()])

        if op == 0xCB: self.__decodeCB(self.__getUInt8())
        # if op == 0xDB: self.__set(ERROR)
        # if op == 0xEB: self.__set(ERROR)
        if op == 0xFB: self.__set(EI)

        if op == 0xCC: self.__set(CALL, condition=COND_Z, target=self.__getUInt16())
        if op == 0xDC: self.__set(CALL, condition=COND_C, target=self.__getUInt16())
        # if op == 0xEC: self.__set(ERROR)
        # if op == 0xFC: self.__set(ERROR)

        if op == 0xCD: self.__set(CALL, target=self.__getUInt16())
        # if op == 0xDD: self.__set(ERROR)
        # if op == 0xED: self.__set(ERROR)
        # if op == 0xFD: self.__set(ERROR)

        if op == 0xCE: self.__set(ADC, target=A, value=self.__getUInt8())
        if op == 0xDE: self.__set(SBC, target=A, value=self.__getUInt8())
        if op == 0xEE: self.__set(XOR, target=A, value=self.__getUInt8())
        if op == 0xFE: self.__set(CP, target=A, value=self.__getUInt8())

        if op == 0xCF: self.__set(RST, value=0x08)
        if op == 0xDF: self.__set(RST, value=0x18)
        if op == 0xEF: self.__set(RST, value=0x28)
        if op == 0xFF: self.__set(RST, value=0x38)

        assert self.type is not None, "Decode failed for: %04X:%02X" % (address, op)

    def __decodeCB(self, op):
        if (op & 0x07) == 0: self.target = B
        if (op & 0x07) == 1: self.target = C
        if (op & 0x07) == 2: self.target = D
        if (op & 0x07) == 3: self.target = E
        if (op & 0x07) == 4: self.target = H
        if (op & 0x07) == 5: self.target = L
        if (op & 0x07) == 6: self.target = [HL]
        if (op & 0x07) == 7: self.target = A
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
            self.value = (op >> 3) & 0x07
            if (op & 0xC0) == 0x40: self.type = BIT
            if (op & 0xC0) == 0x80: self.type = RES
            if (op & 0xC0) == 0xC0: self.type = SET

    def __set(self, instr_type, *, condition=None, target=None, source=None, value=None):
        self.type = instr_type
        self.condition = condition
        self.target = target
        self.source = source
        self.value = value

    def __getInt8(self):
        self.size += 1
        return struct.unpack("b", self.rom.data[self.address+self.size-1:self.address + self.size])[0]

    def __getUInt8(self):
        self.size += 1
        return struct.unpack("B", self.rom.data[self.address+self.size-1:self.address + self.size])[0]

    def __getUInt16(self):
        self.size += 2
        return struct.unpack("<H", self.rom.data[self.address + self.size - 2:self.address + self.size])[0]

    def hasNext(self):
        if self.type in (JP, JR, RET) and self.condition is None:
            return False
        if self.type == RETI:
            return False
        return True

    def jumpTarget(self):
        if self.type in (CALL, JP, JR) and self.target != HL:
            return self.target
        return None

    def format(self, symbol_table):
        if self.type in (JP, CALL, JR):
            target = symbol_table.get(self.target, "$%04x" % (self.target))
            if self.condition:
                return self.__format(self.condition, target)
            return self.__format(target)
        if self.type in (PUSH, POP):
            return self.__format(self.target)
        if self.type in (DEC, INC, XOR, AND, OR, SUB, CP, SBC, ADC):
            return self.__format(self.target)
        if self.type in (LD):
            if self.value is not None:
                if len(self.target) > 1:
                    return self.__format(self.target, "$%04x" % self.value)
                return self.__format(self.target, "$%02x" % self.value)
            return self.__format(self.target, self.source)
        if self.type in (LDH):
            if self.target == A:
                return self.__format(self.target, "[$%04x]" % (self.source))
            return self.__format("[$%04x]" % (self.target), self.source)
        return self.__format()

    def __format(self, param1=None, param2=None):
        if param1 is None:
            return "%s" % (self.type)
        if param2 is None:
            return "%-4s %s" % (self.type, param1)
        return "%-4s %s, %s" % (self.type, param1, param2)

    def __repr__(self):
        return "%s %s %s %s %s" % (self.type, self.condition, self.target, self.source, self.value)
