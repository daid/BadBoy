from rom import ROM
from instruction import Instruction
from instrumentation import Instrumentation
import instruction
import struct
import PIL.Image
import argparse


def exportAllAsGraphics(rom):
    bank_count = len(rom.data) // 0x4000
    result = PIL.Image.new("P", (8 * 16 * bank_count, 64 * 8))

    buffer = bytearray(b'\x00' * 8 * 8)
    for bank in range(bank_count):
        for tile_y in range(64):
            for tile_x in range(16):
                idx = bank * 0x4000 + tile_y * 16 * 16 + tile_x * 16
                print(hex(idx))
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

    def loadInstrumentation(self, filename):
        self.info.load(filename)

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

    def walkInstructionBlocks(self):
        while self.instr_addr_todo:
            self._walkInstructionBlock(self.instr_addr_todo.pop())

    def _walkInstructionBlock(self, addr):
        a_value = None
        active_bank = None
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

            if instr.type == instruction.RST and instr.p0 == args.rstJumpTable:
                addr += 1
                while True:
                    if info.hasMark(addr, info.MARK_INSTR):
                        break
                    target = struct.unpack("<H", self.rom.data[addr:addr + 2])[0]
                    if 0x4000 <= target < 0x8000:
                        target = (target & 0x3FFF) | (addr & 0xFFFFC000)
                    info.mark(addr, info.MARK_DATA | info.MARK_PTR_LOW)
                    info.mark(addr + 1, info.MARK_DATA | info.MARK_PTR_HIGH)
                    info.mark(target, info.MARK_INSTR)
                    info.addAbsoluteRomSymbol(target)
                    todo.append(target)
                    addr += 2
                break

            if not instr.hasNext():
                break
            addr += instr.size


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=str)
    parser.add_argument("--rstJumpTable", type=int, default=None)
    parser.add_argument("--instrumentation", action='append', default=[])
    args = parser.parse_args()

    dis = Disassembler(args.rom)
    for filename in args.instrumentation:
        dis.loadInstrumentation(filename)

    dis.parseFullRom()
    dis.walkInstructionBlocks()

    dis.info.updateSymbols()
    dis.info.dumpStats()

    output = open("out.asm", "wt")
    def out(addr, size, data, is_data=False):
        bank = addr >> 14
        sub_addr = addr
        if bank > 0:
            sub_addr = (addr & 0x3FFF) | 0x4000
        output.write("    %-50s ;; $%02x:$%04x" % (data, bank, sub_addr))
        if is_data:
            output.write(" ")
            for n in range(size):
                output.write(dis.info.classifyData(addr+n))
        else:
            for n in range(size):
                output.write(" $%02x" % (dis.rom.data[addr+n]))
        output.write("\n")

    addr = 0
    dis.info.outputRegs(output)
    dis.info.outputRam(output)
    output.write("""
ld_long_load: MACRO
    db $FA
    dw \\1
ENDM
ld_long_store: MACRO
    db $EA
    dw \\1
ENDM
""")
    for bank in range(len(dis.rom.data) // 0x4000):
        if bank == 0:
            output.write("\nSECTION \"bank00\", ROM0[$0000]\n")
        else:
            output.write("\nSECTION \"bank%02x\", ROMX[$4000], BANK[$%02x]\n" % (bank, bank))
        addr = 0x4000 * bank
        end_of_bank = addr + 0x4000
        while end_of_bank > addr and dis.rom.data[end_of_bank-1] == 0x00:
            end_of_bank -= 1
        while addr < end_of_bank:
            if addr in dis.info.rom_symbols:
                if not dis.info.rom_symbols[addr].startswith("."):
                    output.write("\n")
                output.write("%s:\n" % (dis.info.rom_symbols[addr]))
            if dis.info.hasMark(addr, dis.info.MARK_INSTR):
                instr = Instruction(dis.rom, addr)
                out(addr, instr.size, instr.format(dis.info))
                addr += instr.size
            elif dis.info.hasMark(addr, dis.info.MARK_PTR_LOW) and dis.info.hasMark(addr + 1, dis.info.MARK_PTR_HIGH):
                pointer = dis.rom.data[addr] | (dis.rom.data[addr+1] << 8)
                size = 2
                out(addr, size, "dw   %s" % dis.info.formatParameter(addr, pointer))
                addr += size
            else:
                size = 1
                while size < 8 and addr + size < end_of_bank and addr + size not in dis.info.rom_symbols and not (dis.info.hasMark(addr + size, dis.info.MARK_INSTR) or dis.info.hasMark(addr + size, dis.info.MARK_PTR_LOW)):
                    size += 1
                if dis.info.hasMark(addr - 1, dis.info.MARK_INSTR) and not any(dis.rom.data[addr:addr+size]):
                    while addr + size < end_of_bank and not (dis.info.hasMark(addr + size, dis.info.MARK_INSTR) or dis.info.hasMark(addr + size, dis.info.MARK_PTR_LOW)) and dis.rom.data[addr+size] == 0 and addr + size not in dis.info.rom_symbols:
                        size += 1
                    out(addr, 0, "ds   %d" % (size))
                else:
                    out(addr, size, "db   " + ", ".join(map(lambda n: "$%02x" % (n), dis.rom.data[addr:addr+size])), is_data=True)
                addr += size
