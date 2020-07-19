from rom import ROM
from instruction import Instruction
from instrumentation import Instrumentation
import instruction
import annotations
import struct
import PIL.Image
import argparse
import os


def exportAllAsGraphics(rom):
    bank_count = len(rom.data) // 0x4000
    result = PIL.Image.new("P", (8 * 16 * bank_count, 64 * 8))

    buffer = bytearray(b'\x00' * 8 * 8)
    for bank in range(bank_count):
        for tile_y in range(64):
            for tile_x in range(16):
                idx = bank * 0x4000 + tile_y * 16 * 16 + tile_x * 16
                for y in range(8):
                    a = rom.data[idx + y * 2]
                    b = rom.data[idx + y * 2 + 1]
                    for x in range(8):
                        v = 0
                        if a & (0x80 >> x):
                            v |= 1
                        if b & (0x80 >> x):
                            v |= 2
                        buffer[x+y*8] = v
                tile = PIL.Image.frombytes('P', (8, 8), bytes(buffer))
                result.paste(tile, (bank * 16 * 8 + tile_x * 8, tile_y * 8))

    pal = result.getpalette()
    pal[0:3] = [0x2d,0x1b,0x00]
    pal[3:6] = [0x1e,0x60,0x6e]
    pal[6:9] = [0x5a,0xb9,0xa8]
    pal[9:12] = [0xc4,0xf0,0xc2]
    result.putpalette(pal)
    result.save("output.png")


def exportAllStrings(rom):
    char_map = ["<%02x>" % n for n in range(256)]
    for n in range(10):
        char_map[0xB0 + n] = str(n)
    for n in range(26):
        char_map[0xBA + n] = chr(65 + n)
        char_map[0xD4 + n] = chr(97 + n)
    char_map[0x1A] = "\\n"
    char_map[0xEE] = "'"
    char_map[0xEF] = ","
    char_map[0xF0] = "."
    char_map[0xF1] = "_"
    char_map[0xF2] = "-"
    char_map[0xF3] = "!"
    char_map[0xF4] = "?"
    char_map[0xF5] = ":"
    char_map[0xF6] = "/"
    char_map[0xFF] = " "
    for n in range(0x80):
        d0 = rom.data[0x3F1D + n * 2]
        d1 = rom.data[0x3F1D + n * 2 + 1]
        if 0x30 + n >= 0x80:
            char_map[0x30 + n] = char_map[d0] + char_map[d1]
        else:
            char_map[0x20 + n] = char_map[d0] + char_map[d1]
        # char_map[0x30 + n] = "<%02x:%02x:%02x>" % (n, d0, d1)

    f = open("output.txt", "wt")
    for addr, byte in enumerate(rom.data):
        if addr % 32 == 0:
            f.write("\n%02x:%04x:" % (addr >> 14, (addr & 0x3FFF) | (0x4000 if addr > 0x4000 else 0x0000)))
        f.write(char_map[byte])


class Disassembler:
    def __init__(self, rom_file):
        self.rom = ROM(rom_file)
        self.info = Instrumentation(self.rom)

        self.instr_addr_done = set()
        self.instr_addr_todo = [0x0100, 0x0000, 0x0040, 0x0048, 0x0050, 0x0058, 0x0060]
        self.rstJumpTable = None

        self.formatter = {}

    def loadInstrumentation(self, filename):
        self.info.loadInstrumentation(filename)

    def loadSymbolFile(self, filename):
        self.info.loadSymbolFile(filename)

    def loadSource(self, filename):
        self.info.loadSource(filename)

    def parseFullRom(self):
        for addr in range(len(self.rom.data)):
            if self.info.getMarks(addr, self.info.MARK_INSTR | self.info.MARK_DATA) == self.info.MARK_INSTR:
                self.instr_addr_todo.append(addr)
            elif self.info.hasMark(addr, self.info.MARK_PTR_LOW) and self.info.hasMark(addr + 1, self.info.MARK_PTR_HIGH):
                target = struct.unpack("<H", self.rom.data[addr:addr + 2])[0]
                if target < 0x4000:
                    self.info.addAbsoluteRomSymbol(target)
                elif target < 0x8000:
                    # TODO: Instrumentation could store the active bank instead of assuming the pointer points to
                    #       the bank where the pointer is in.
                    self.info.addAbsoluteRomSymbol((target & 0x3FFF) | (addr & 0xFFFFC000))
        for addr in range(0, len(self.rom.data), 0x4000):
            self.info.addAbsoluteRomSymbol(addr)

    def processAnnotations(self):
        for addr, annos in self.info.annotations.items():
            for annotation in annos:
                annotations.ALL[annotation[0].lower()](self, addr, annotation[1:])

    def walkInstructionBlocks(self):
        while self.instr_addr_todo:
            self._walkInstructionBlock(self.instr_addr_todo.pop())

    def _walkInstructionBlock(self, addr):
        a_value = None
        active_bank = None if self.rom.bankCount() > 2 else 1
        info = self.info

        while True:
            if addr in self.instr_addr_done:
                break
            self.instr_addr_done.add(addr)
            instr = Instruction(self.rom, addr)
            active_bank = info.getActiveBank(addr) or active_bank

            info.mark(addr, info.MARK_INSTR)
            for n in range(1, instr.size):
                info.mark(addr + n, info.MARK_INSTR | info.MARK_DATA)

            target = instr.jumpTarget(active_bank)
            if target:
                if instr.type == instruction.JR:
                    info.addAbsoluteRomSymbol(target, addr)
                else:
                    info.addAbsoluteRomSymbol(target)
                self.instr_addr_todo.append(target)
            elif isinstance(instr.p0, instruction.Word):
                info.addRelativeSymbol(instr.p0.value, addr)
            elif isinstance(instr.p1, instruction.Word):
                info.addRelativeSymbol(instr.p1.value, addr)
            elif isinstance(instr.p0, instruction.Ref) and isinstance(instr.p0.target, instruction.Word):
                info.addRelativeSymbol(instr.p0.target.value, addr)
            elif isinstance(instr.p1, instruction.Ref) and isinstance(instr.p1.target, instruction.Word):
                info.addRelativeSymbol(instr.p1.target.value, addr)

            if instr.type == instruction.LD and instr.p0 == instruction.A:
                a_value = instr.p1 if isinstance(instr.p1, int) else None
            if instr.type == instruction.LD and instr.p1 == instruction.A and isinstance(instr.p0, instruction.Ref) and isinstance(instr.p0.target, instruction.Word) and instr.p0.target.value == 0x2100:
                active_bank = a_value

            if instr.type == instruction.RST and instr.p0 == self.rstJumpTable:
                addr += 1
                while True:
                    if info.hasMark(addr, info.MARK_INSTR):
                        break
                    target = info.markAsCodePointer(self.rom, addr)
                    if target is not None:
                        self.instr_addr_todo.append(target)
                    addr += 2
                break

            if not instr.hasNext():
                break
            addr += instr.size

    def export(self, path):
        os.makedirs(os.path.join(path, "src"), exist_ok=True)
        os.makedirs(os.path.join(path, "constants"), exist_ok=True)
        os.makedirs(os.path.join(path, "gfx"), exist_ok=True)
        main = open(os.path.join(path, "src", "main.asm"), "wt")
        main.write("include \"constants/regs.asm\"\n")
        main.write("include \"constants/memory.asm\"\n")
        main.write("include \"src/macros.asm\"\n")

        self.info.outputRegs(open(os.path.join(path, "constants", "regs.asm"), "wt"))
        self.info.outputRam(open(os.path.join(path, "constants", "memory.asm"), "wt"))
        open(os.path.join(path, "src", "macros.asm"), "wt").write("""
ld_long_load: MACRO
    db $FA
    dw \\1
ENDM
ld_long_store: MACRO
    db $EA
    dw \\1
ENDM
bad_halt: MACRO
    db $76
ENDM
""")
        open(os.path.join(path, "Makefile"), "wt").write("""
ASM_FILES = $(shell find -type f -name '*.asm')

rom.gb: src/main.o
\trgblink -n $(basename $@).sym -o $@ $^
\trgbfix --validate $@

src/main.o: $(ASM_FILES)
\trgbasm --export-all -o $@ src/main.asm

check: rom.gb rom.md5
\tmd5sum -c rom.md5

clean:
\trm -rf src/main.o rom.gb rom.sym

.PHONY: all clean check
all: rom.gb
""")
        open(os.path.join(path, "rom.md5"), "wt").write("%s rom.gb\n" % (self.rom.md5sum()))
        for bank in range(len(self.rom.data) // 0x4000):
            if bank == 0:
                main.write("\nSECTION \"bank00\", ROM0[$0000]\n")
            else:
                main.write("\nSECTION \"bank%02x\", ROMX[$4000], BANK[$%02x]\n" % (bank, bank))
            main.write("include \"src/bank%02X.asm\"\n" % (bank))
            self._writeBank(bank, open(os.path.join(path, "src", "bank%02X.asm" % (bank)), "wt"))

    def _writeBank(self, bank, output):
        output.write(";; Disassembled with BadBoy Disassembler: https://github.com/daid/BadBoy\n")
        addr = 0x4000 * bank
        end_of_bank = addr + 0x4000
        while end_of_bank > addr and self.rom.data[end_of_bank-1] == 0x00:
            end_of_bank -= 1
        while addr < end_of_bank:
            if addr in self.info.rom_symbols and "." not in self.info.rom_symbols[addr]:
                output.write("\n")
            if addr in self.info.annotations:
                for annotation in self.info.annotations[addr]:
                    output.write(";@%s\n" % (": ".join(annotation)))
            if addr in self.info.comments:
                for comment in self.info.comments[addr]:
                    output.write(";%s\n" % (comment))
            if addr in self.info.rom_symbols:
                symbol = self.info.rom_symbols[addr]
                output.write("%s:\n" % self.info.formatSymbol(symbol))

            formatter = self.getFormatter(addr)
            addr = formatter(output, addr)

    def getFormatter(self, addr):
        if addr in self.formatter:
            return self.formatter[addr]
        if self.info.hasMark(addr, self.info.MARK_INSTR):
            return self.__formatInstruction
        elif self.info.hasMark(addr, self.info.MARK_PTR_LOW) and self.info.hasMark(addr + 1, self.info.MARK_PTR_HIGH):
            return self.__formatPointer
        elif self.info.hasMark(addr, self.info.MARK_WORD_LOW) and self.info.hasMark(addr + 1, self.info.MARK_WORD_HIGH):
            return self.__formatWord
        elif self.info.classifyDataAsChar(addr) == "G" and self.info.classifyDataAsChar(addr + 1) == "G":
            return self.__formatGraphics
        return self.__formatRawData

    def __formatInstruction(self, output, addr):
        instr = Instruction(self.rom, addr)
        self.formatLine(output, addr, instr.size, instr.format(self.info))
        return addr + instr.size

    def __formatWord(self, output, addr):
        value = struct.unpack("<H", self.rom.data[addr:addr + 2])[0]
        self.formatLine(output, addr, 2, "dw   $%04x" % (value))
        return addr + 2

    def __formatPointer(self, output, addr):
        pointer = struct.unpack("<H", self.rom.data[addr:addr + 2])[0]
        self.formatLine(output, addr, 2, "dw   %s" % self.info.formatParameter(addr, pointer, is_word=True))
        return addr + 2

    def __formatGraphics(self, output, addr):
        a = self.rom.data[addr+0]
        b = self.rom.data[addr+1]
        gfx = ""
        for n in range(8):
            p = 0
            if a & (0x80 >> n):
                p |= 1
            if b & (0x80 >> n):
                p |= 2
            gfx += "%d" % p
        self.formatLine(output, addr, 2, "dw   `%s" % gfx)
        return addr + 2

    def __formatRawData(self, output, addr):
        size = 1
        end_of_bank = (addr | 0x3FFF) + 1
        while size < 8 and addr + size < end_of_bank and addr + size not in self.info.rom_symbols and self.getFormatter(addr + size) == self.__formatRawData:
            size += 1
        if self.info.hasMark(addr - 1, self.info.MARK_INSTR) and not any(self.rom.data[addr:addr + size]):
            while addr + size < end_of_bank and self.getFormatter(addr + size) == self.__formatRawData and self.rom.data[addr + size] == 0 and addr + size not in self.info.rom_symbols:
                size += 1
            self.formatLine(output, addr, size, "ds   %d" % (size), is_data=True)
        else:
            self.formatLine(output, addr, size, "db   " + ", ".join(map(lambda n: "$%02x" % (n), self.rom.data[addr:addr + size])), is_data=True)
        return addr + size

    def formatLine(self, output, address, size, line, is_data=False):
        bank = address >> 14
        sub_address = address
        if bank > 0:
            sub_address = (address & 0x3FFF) | 0x4000
        output.write("    %-50s ;; %02x:%04x" % (line, bank, sub_address))
        if is_data:
            output.write(" ")
            for n in range(size):
                output.write(self.info.classifyDataAsChar(address+n))
        else:
            for n in range(size):
                output.write(" $%02x" % (self.rom.data[address+n]))
            for n in range(size):
                s = self.info.classifyData(address+n)
                if s:
                    output.write(" %s" % (s))
        output.write("\n")


if __name__ == "__main__":
    import sys
    import os
    import importlib
    import pkgutil

    sys.path.append(os.path.join(os.getcwd(), "plugins"))
    for module in pkgutil.iter_modules():
        if module.name.startswith("badboy_"):
            importlib.import_module(module.name)

    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=str)
    parser.add_argument("--rstJumpTable", type=str, default=None)
    parser.add_argument("--instrumentation", action='append', default=[])
    parser.add_argument("--sym")
    parser.add_argument("--source")
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    dis = Disassembler(args.rom)
    if args.rstJumpTable:
        dis.rstJumpTable = int(args.rstJumpTable, 16)
    for filename in args.instrumentation:
        dis.loadInstrumentation(filename)
    if args.sym:
        dis.loadSymbolFile(args.sym)
    if args.source:
        dis.loadSource(args.source)
    dis.parseFullRom()
    dis.processAnnotations()
    dis.walkInstructionBlocks()

    dis.info.updateSymbols()
    dis.info.dumpStats()

    dis.export(args.output)
