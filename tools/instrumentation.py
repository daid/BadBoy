import struct
from instruction import Ref, Word


class AutoSymbol:
    def __init__(self, address=None):
        self.source_min = address
        self.source_max = address

    def setAsGlobalSymbol(self):
        self.source_min = None
        self.source_max = None

    def addLocalSource(self, address):
        if self.source_min is None:
            return
        self.source_min = min(self.source_min, address)
        self.source_max = min(self.source_max, address)

    def __repr__(self):
        return "AutoSymbol<%s:%s>" % (self.source_min, self.source_max)


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
        self.rom_symbols = {
            0x0000: "rst_00",
            0x0008: "rst_08",
            0x0010: "rst_10",
            0x0018: "rst_18",
            0x0020: "rst_20",
            0x0028: "rst_28",
            0x0030: "rst_30",
            0x0038: "rst_38",
            0x0040: "VBlankInterrupt",
            0x0048: "LCDCInterrupt",
            0x0050: "TimerOverflowInterrupt",
            0x0058: "SerialTransferInterrupt",
            0x0060: "JoypadInterrupt",
            0x0100: "Reset",
            0x0104: "Header",
        }
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

    def addRomSymbol(self, address, source_address=None):
        symbol = self.rom_symbols.get(address, None)
        if not symbol:
            symbol = AutoSymbol(source_address)
            self.rom_symbols[address] = symbol
        if isinstance(symbol, AutoSymbol):
            if source_address is not None:
                symbol.addLocalSource(source_address)
            else:
                symbol.setAsGlobalSymbol()

    def updateSymbols(self):
        last_symbol_addr = 0
        for addr in range(len(self.rom)):
            if addr not in self.rom_symbols:
                continue
            symbol = self.rom_symbols[addr]
            if isinstance(symbol, AutoSymbol):
                bank = addr >> 14
                local_addr = (addr & 0x3FFF) | (0x4000 if bank > 0 else 0x0000)
                if symbol.source_min is not None and symbol.source_min > last_symbol_addr:
                    symbol = ".jr_%03x_%04x" % (bank, local_addr)
                else:
                    symbol = "jr_%03x_%04x" % (bank, local_addr)
                self.rom_symbols[addr] = symbol
            if not symbol.startswith("."):
                last_symbol_addr = addr


    def load(self, filename):
        f = open(filename, "rb")
        while True:
            data = f.read(16)
            if not data:
                break
            source, used_as = struct.unpack("<QQ", data)
            if (source & self.ID_MASK) == self.ID_ROM:
                self.rom[source & 0xFFFFFFFF] = used_as

    def formatParameter(self, base_address, parameter, *, pc_target=False):
        if isinstance(parameter, Ref):
            return "[%s]" % (self.formatParameter(base_address, parameter.target, pc_target=pc_target))
        if isinstance(parameter, Word):
            return self.formatParameter(base_address, parameter.target, pc_target=pc_target)
        if isinstance(parameter, int):
            if not pc_target and parameter in self.reg_symbols:
                return self.reg_symbols[parameter]
            if parameter >= 0x8000 and parameter in self.ram_symbols:
                return self.ram_symbols[parameter]
            if (parameter >= 0x1000 or pc_target) and parameter < 0x4000 and parameter in self.rom_symbols:
                return self.rom_symbols[parameter]
            if parameter >= 0x4000 and parameter < 0x8000 and base_address >= 0x4000:  # upper bank target
                addr = (parameter & 0x3FFF) | (base_address & 0xFFFFC000)
                if addr in self.rom_symbols:
                    return self.rom_symbols[addr]
            return "$%02x" % (parameter)
        return parameter

    def outputRegs(self, file):
        for value, name in self.reg_symbols.items():
            file.write("%-14s EQU $%04x\n" % (name, value))

    def dumpStats(self):
        total = {}
        for bank in range(len(self.rom) // 0x4000):
            stats = {}
            start = bank*0x4000
            end = start+0x4000
            for addr in range(start, end):
                mark = self.rom[addr]
                basic_type = 'unknown'
                if mark & self.MARK_INSTR:
                    basic_type = 'instruction'
                elif (mark & self.MARK_DATA) and (mark & self.ID_MASK) == self.ID_VRAM:
                    if (mark & 0xFFFF) < 0x1800:
                        basic_type = 'vram:tile'
                    else:
                        basic_type = 'vram:data'
                elif mark & self.MARK_DATA:
                    basic_type = 'data'
                stats[basic_type] = stats.get(basic_type, 0) + 1
                total[basic_type] = total.get(basic_type, 0) + 1
            print("Bank: %02x" % (bank))
            for k, v in sorted(stats.items()):
                print("  %s: %d (%f%%)" % (k, v, v * 100 / 0x4000))
        print("Total:")
        for k, v in sorted(total.items()):
            print("  %s: %d (%f%%)" % (k, v, v * 100 / len(self.rom)))
