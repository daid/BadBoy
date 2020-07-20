import struct
from instruction import Ref, Word
import re
import os


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
        self.source_max = max(self.source_max, address)

    def isGlobal(self):
        return self.source_min is None

    def format(self, addr, flags, *, scope=None):
        bank = addr >> 14
        addr &= 0x3FFF
        if bank > 0:
            addr |= 0x4000
        type_name = "unknown"
        if flags & Instrumentation.MARK_INSTR:
            type_name = "code"
        if flags & Instrumentation.MARK_DATA:
            type_name = "data"
        if self.source_min is not None:
            return "%s.%s_%04x" % (scope, type_name, addr)
        return "%s_%03x_%04x" % (type_name, bank, addr)

    def __repr__(self):
        return "AutoSymbol<%x:%x>" % (self.source_min, self.source_max)


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
    MARK_WORD_LOW = (0x10 << 40)
    MARK_WORD_HIGH = (0x20 << 40)
    MARK_BANK_SHIFT = (48)
    MARK_BANK_MASK = (0xFFF << 48)

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
            0x0104: "HeaderLogo",
            0x0134: "HeaderTitle",
            0x0143: "HeaderGBCFlag",
            0x0144: "HeaderNewLicenseCode",
            0x0146: "HeaderSGBFlag",
            0x0147: "HeaderCardType",
            0x0148: "HeaderRomSize",
            0x0149: "HeaderRamSize",
            0x014A: "HeaderWorldOrJapanFlag",
            0x014B: "HeaderLicenseCode",
            0x014C: "HeaderROMVersion",
            0x014D: "HeaderChecksum",
            0x014E: "HeaderGlobalChecksum",
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
        self.annotations = {}
        self.comments = {}

    def mark(self, address, mark):
        self.rom[address] |= mark

    def getMarks(self, address, marks):
        return self.rom[address] & marks

    def hasMark(self, address, mark):
        return (self.rom[address] & mark) == mark

    def markAsWord(self, rom, address, *, name=None):
        self.mark(address, self.MARK_DATA | self.MARK_WORD_LOW)
        self.mark(address + 1, self.MARK_DATA | self.MARK_WORD_HIGH)
        return struct.unpack("<H", rom.data[address:address+2])[0]

    def markAsPointer(self, rom, address, *, name=None):
        target = struct.unpack("<H", rom.data[address:address+2])[0]

        if 0x4000 <= target < 0x8000:
            if address < 0x4000:
                return None
            target = (target & 0x3FFF) | (address & 0xFFFFC000)
        elif target >= 0x8000:
            return None

        self.mark(address, self.MARK_DATA | self.MARK_PTR_LOW)
        self.mark(address + 1, self.MARK_DATA | self.MARK_PTR_HIGH)
        self.addAbsoluteRomSymbol(target, name=name)
        return target

    def markAsCodePointer(self, rom, address, name=None):
        target = struct.unpack("<H", rom.data[address:address+2])[0]

        if 0x4000 <= target < 0x8000:
            if address < 0x4000:
                return None
            target = (target & 0x3FFF) | (address & 0xFFFFC000)
        elif target >= 0x8000:
            return None

        self.mark(address, self.MARK_DATA | self.MARK_PTR_LOW)
        self.mark(address + 1, self.MARK_DATA | self.MARK_PTR_HIGH)
        self.mark(target, self.MARK_INSTR)
        self.addAbsoluteRomSymbol(target, name=name)
        return target

    def getActiveBank(self, addr):
        bank = (self.rom[addr] & self.MARK_BANK_MASK) >> self.MARK_BANK_SHIFT
        if bank == 0:
            return None
        return bank

    def setActiveBank(self, addr, bank):
        self.rom[addr] = (self.rom[addr] & ~self.MARK_BANK_MASK) | (bank << self.MARK_BANK_SHIFT)

    def classifyData(self, addr):
        mark = self.rom[addr]
        if not (mark & self.MARK_DATA):
            return None
        id = mark & self.ID_MASK
        if id == self.ID_VRAM:
            if (mark & 0x3FFF) < 0x1800:
                return "GFX"
            return "BackgroundTile"
        elif id == self.ID_OAM:
            if (mark & 0x03) == 0x00:
                return "Sprite X"
            if (mark & 0x03) == 0x01:
                return "Sprite Y"
            if (mark & 0x03) == 0x02:
                return "Sprite Tile"
            return "Sprite Attribute"
        elif id == self.ID_IO:
            return self.reg_symbols.get(mark & 0xFFFF, "Reg[%04x]" % (mark & 0xFFFF))
        elif id == self.ID_ROM:
            if (mark & 0xF000) == 0x2000:
                return "Bank"
        return None

    def classifyDataAsChar(self, addr):
        mark = self.rom[addr]
        if not (mark & self.MARK_DATA):
            return "?"
        id = mark & self.ID_MASK
        if id == self.ID_VRAM:
            if (mark & 0x3FFF) < 0x1800:
                return "G"
            return "V"
        elif id == self.ID_OAM:
            if (mark & 0x03) == 0x00:
                return "Y"
            if (mark & 0x03) == 0x01:
                return "X"
            if (mark & 0x03) == 0x02:
                return "T"
            return "A"
        elif id == self.ID_IO:
            if 0xFF10 <= (mark & 0xFFFF) < 0xFF30:
                return "S"
            if 0xFF30 <= (mark & 0xFFFF) < 0xFF40:
                return "W"
            return "R"
        return "."

    def addRamSymbol(self, address):
        if address not in self.ram_symbols:
            if address >= 0xFF80:
                self.ram_symbols[address] = "h%04X" % (address)
            else:
                self.ram_symbols[address] = "w%04X" % (address)

    def addAbsoluteRomSymbol(self, address, source_address=None, *, name=None):
        symbol = self.rom_symbols.get(address, None)
        if not symbol or name is not None:
            if name is not None:
                symbol = name
            else:
                symbol = AutoSymbol(address)
            self.rom_symbols[address] = symbol
        if isinstance(symbol, AutoSymbol):
            if source_address is not None:
                symbol.addLocalSource(source_address)
            else:
                symbol.setAsGlobalSymbol()

    def addRelativeSymbol(self, address, source_address, *, name=None):
        if address < 0x0400:
            if source_address >= 0x4000:
                return
            if abs(address - source_address) > 0x100:
                return
        if 0xC000 <= address < 0xE000:
            self.addRamSymbol(address)
        if 0xFF80 <= address < 0xFFFF:
            self.addRamSymbol(address)
        if address >= 0x8000:
            return
        if address >= 0x4000:
            if source_address < 0x4000:
                return
            address = (address & 0x3fff) | (source_address & 0xFFFFC000)
        self.addAbsoluteRomSymbol(address, name=name)

    def updateSymbols(self):
        changes = True
        while changes:
            changes = False
            last_symbol_addr = 0
            for addr, symbol in sorted(self.rom_symbols.items()):
                if isinstance(symbol, AutoSymbol):
                    if not symbol.isGlobal() and last_symbol_addr > symbol.source_min:
                        symbol.setAsGlobalSymbol()
                        changes = True
                    if symbol.isGlobal():
                        last_symbol_addr = addr
                elif not symbol.startswith("."):
                    last_symbol_addr = addr
            for addr, symbol in sorted(self.rom_symbols.items(), reverse=True):
                if isinstance(symbol, AutoSymbol):
                    if not symbol.isGlobal() and last_symbol_addr < symbol.source_max:
                        symbol.setAsGlobalSymbol()
                        changes = True
                    if symbol.isGlobal():
                        last_symbol_addr = addr
                elif not symbol.startswith("."):
                    last_symbol_addr = addr

        new_symbols = {}
        scope = None
        for addr, symbol in sorted(self.rom_symbols.items()):
            if not self.hasMark(addr, self.MARK_INSTR | self.MARK_DATA):
                if isinstance(symbol, AutoSymbol):
                    new_symbols[addr] = symbol.format(addr, self.rom[addr], scope=scope)
                else:
                    new_symbols[addr] = symbol
                if "." not in new_symbols[addr]:
                    scope = new_symbols[addr]
            else:
                print("drop %04x" % (addr))
        self.rom_symbols = new_symbols

    def loadInstrumentation(self, filename):
        f = open(filename, "rb")
        while True:
            data = f.read(16)
            if not data:
                break
            source, used_as = struct.unpack("<QQ", data)
            if (source & self.ID_MASK) == self.ID_ROM:
                self.rom[source & 0xFFFFFFFF] = used_as

    def loadSymbolFile(self, filename):
        for line in open(filename, "rt"):
            line = line.strip()
            if line.startswith(";"):
                continue
            addr, symbol = line.split(" ", 1)
            bank, addr = addr.split(":", 1)
            bank, addr, symbol = int(bank, 16), int(addr, 16), symbol.strip()
            if re.match(r"(unknown|code|data)_[0-9a-fA-F]{3}_[0-9a-fA-F]{4}$", symbol):
                continue
            if re.match(r"(unknown|code|data)_[0-9a-fA-F]{3}_[0-9a-fA-F]{4}\.(unknown|code|data)_[0-9a-fA-F]{4}$", symbol):
                continue
            if re.match(r"[wh][0-9A-F]{4}$", symbol):
                continue
            if addr < 0x4000:
                assert bank == 0
                self.rom_symbols[addr] = symbol
            elif addr < 0x8000:
                self.rom_symbols[(addr & 0x3FFF) | (bank << 14)] = symbol
            elif addr < 0xA000:
                pass  # TODO VRAM
            elif addr < 0xC000:
                pass  # TODO SRAM
            elif addr < 0xD000:
                assert bank == 0
                self.ram_symbols[addr] = symbol
            elif addr < 0xE000:
                self.ram_symbols[addr] = symbol
            elif addr < 0xFF80:
                pass  # IO regs, mirror, oam
            elif addr < 0xFFFF:
                self.ram_symbols[addr] = symbol

    def formatParameter(self, base_address, parameter, *, pc_target=False, is_word=False, is_pointer=False):
        if isinstance(parameter, Ref):
            return "[%s]" % (self.formatParameter(base_address, parameter.target, pc_target=pc_target, is_pointer=is_pointer))
        if isinstance(parameter, Word):
            return self.formatParameter(base_address, parameter.value, pc_target=pc_target, is_word=True, is_pointer=is_pointer)
        if isinstance(parameter, int):
            if not pc_target and parameter in self.reg_symbols:
                return self.formatSymbol(self.reg_symbols[parameter])
            if parameter >= 0x8000 and parameter in self.ram_symbols:
                return self.formatSymbol(self.ram_symbols[parameter])
            if (parameter >= 0x1000 or pc_target or is_pointer) and parameter < 0x4000 and parameter in self.rom_symbols:
                return self.formatSymbol(self.rom_symbols[parameter])
            if 0x4000 <= parameter < 0x8000 and self.getActiveBank(base_address) is not None:
                addr = (parameter & 0x3FFF) | (self.getActiveBank(base_address) << 14)
                if addr in self.rom_symbols:
                    return self.formatSymbol(self.rom_symbols[addr])
            elif 0x4000 <= parameter < 0x8000 and base_address >= 0x4000:  # upper bank target
                addr = (parameter & 0x3FFF) | (base_address & 0xFFFFC000)
                if addr in self.rom_symbols:
                    return self.formatSymbol(self.rom_symbols[addr])
            if is_word:
                return "$%04x" % (parameter)
            return "$%02x" % (parameter)
        return parameter

    def formatSymbol(self, symbol):
        if "." in symbol:
            return symbol[symbol.find("."):]
        return symbol

    def outputRegs(self, file):
        for value, name in sorted(self.reg_symbols.items()):
            file.write("%-14s EQU $%04x\n" % (name, value))

    def loadSource(self, source_file):
        collected_annotations = []
        collected_comments = []
        for line in open(source_file, "rt"):
            m = re.match("include \"([^\"]+)\"", line)
            if m:
                path = source_file
                while True:
                    path = os.path.dirname(path)
                    if os.path.isfile(os.path.join(path, m.group(1))):
                        self.loadSource(os.path.join(path, m.group(1)))
                        break
                    assert path != "", "Could not find include: %s" % (m.group(1))

            m = re.search(r";@(.+)", line)
            if m:
                annotation = [s.strip() for s in m.group(1).strip().split(":")]
                collected_annotations.append(annotation)
            m = re.search(r"(^|[^;]);([^@;].+)", line)
            if m:
                comment = m.group(2)
                if ";;" in comment:
                    comment = comment[:comment.find(";;")]
                collected_comments.append(comment)

            m = re.search(r";; ([0-9A-Fa-f]{2}):([0-9A-Fa-f]{4})", line)
            if m:
                addr = (int(m.group(2), 16) & 0x3fff) | (int(m.group(1), 16) << 14)
                if collected_annotations:
                    self.annotations[addr] = collected_annotations
                    collected_annotations = []
                if collected_comments:
                    self.comments[addr] = collected_comments
                    collected_comments = []

        assert len(collected_annotations) == 0


    def outputRam(self, file):
        file.write("\nSECTION \"WRAM Bank0\", WRAM0[$c000]\n")
        addr = 0xC000
        for value, name in sorted(self.ram_symbols.items()):
            if addr < 0xD000 <= value:
                file.write("\nSECTION \"WRAM Bank1\", WRAMX[$d000], BANK[$01]\n")
                addr = 0xD000
            if addr < 0xFF80 <= value:
                file.write("\nSECTION \"HRAM\", HRAM\n")
                addr = 0xFF80
            if addr < value:
                file.write("  ds %d\n" % (value - addr))
            file.write("%s: ;; $%04x\n" % (name, value))
            addr = value

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
