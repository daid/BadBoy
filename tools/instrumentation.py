import struct
from instruction import Ref, Word


class Instrumentation:
    ID_MASK = (0xFF << 32)
    ID_ROM = (0x00 << 32)
    ID_VRAM = (0x01 << 32)
    ID_SRAM = (0x02 << 32)
    ID_WRAM = (0x03 << 32)
    ID_OAM = (0x04 << 32)
    ID_IO = (0x05 << 32)
    ID_HRAM = (0x06 << 32)
    MARK_MASK = (0xFF << 40)
    MARK_INSTR = (0x01 << 40)
    MARK_DATA = (0x02 << 40)
    MARK_PTR_LOW = (0x04 << 40)
    MARK_PTR_HIGH = (0x08 << 40)

    def __init__(self, rom):
        self.rom = [0] * len(rom.data)
        self.rom_symbols = {}
        self.ram_symbols = {}
        self.reg_symbols = {
            0x2100: "MBCBankSelect",

            0xff00: "rP1",
            0xff01: "rSB",
            0xff02: "rSC",
            0xff04: "rDIV",
            0xff05: "rTIMA",
            0xff06: "rTMA",
            0xff07: "rTAC",
            0xff0f: "rIF",
            0xff10: "rNR10",
            0xff11: "rNR11",
            0xff12: "rNR12",
            0xff13: "rNR13",
            0xff14: "rNR14",
            0xff16: "rNR21",
            0xff17: "rNR22",
            0xff18: "rNR23",
            0xff19: "rNR24",
            0xff1a: "rNR30",
            0xff1b: "rNR31",
            0xff1c: "rNR32",
            0xff1d: "rNR33",
            0xff1e: "rNR34",
            0xff20: "rNR41",
            0xff21: "rNR42",
            0xff22: "rNR43",
            0xff23: "rNR44",
            0xff24: "rNR50",
            0xff25: "rNR51",
            0xff26: "rNR52",
            0xff40: "rLCDC",
            0xff41: "rSTAT",
            0xff42: "rSCY",
            0xff43: "rSCX",
            0xff44: "rLY",
            0xff45: "rLYC",
            0xff46: "rDMA",
            0xff47: "rBGP",
            0xff48: "rOBP0",
            0xff49: "rOBP1",
            0xff4a: "rWY",
            0xff4b: "rWX",
            0xff4d: "rKEY1",
            0xff4f: "rVBK",
            0xff51: "rHDMA1",
            0xff52: "rHDMA2",
            0xff53: "rHDMA3",
            0xff54: "rHDMA4",
            0xff55: "rHDMA5",
            0xff56: "rRP",
            0xff68: "rBCPS",
            0xff69: "rBGPD",
            0xff6a: "rOCPS",
            0xff6b: "rOBPD",
            0xff70: "rSVBK",
            0xffff: "rIE",
        }

    def mark(self, address, mark):
        self.rom[address] |= mark

    def hasMark(self, address, mark):
        return (self.rom[address] & mark) == mark

    def load(self, filename):
        f = open("tetris.data", "rb")
        while True:
            data = f.read(16)
            if not data:
                break
            source, used_as = struct.unpack("<QQ", data)
            if (source & self.ID_MASK) == self.ID_ROM:
                self.rom[source & 0xFFFFFFFF] = used_as

    def formatParameter(self, base_address, parameter):
        if isinstance(parameter, Ref):
            return "[%s]" % (self.formatParameter(base_address, parameter.target))
        if isinstance(parameter, Word):
            return self.formatParameter(base_address, parameter.target)
        if isinstance(parameter, int):
            if parameter >= 0x8000 and parameter in self.reg_symbols:
                return self.reg_symbols[parameter]
            if parameter >= 0x8000 and parameter in self.ram_symbols:
                return self.ram_symbols[parameter]
            if parameter < 0x4000 and parameter in self.rom_symbols:
                return self.rom_symbols[parameter]
            return "$%02x" % (parameter)
        return parameter

    def printRegs(self):
        for value, name in self.reg_symbols.items():
            print("%s EQU $%04x" % (name, value))

    def dumpStats(self):
        stats = {}
        for marks in self.rom:
            mark = (marks & self.MARK_MASK) >> 40
            stats[mark] = stats.get(mark, 0) + 1
        print(stats)
