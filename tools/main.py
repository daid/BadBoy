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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=str)
    parser.add_argument("--rstJumpTable", type=int, default=None)
    args = parser.parse_args()
    rom = ROM(args.rom)
    info = Instrumentation(rom)

    done = set()
    todo = [0x0100, 0x0000, 0x0040, 0x0048, 0x0050, 0x0058, 0x0060]

    while todo:
        addr = todo.pop()
        active_bank = None
        a_value = None

        while True:
            if addr in done:
                break
            done.add(addr)
            instr = Instruction(rom, addr)
            info.mark(addr, info.MARK_INSTR)
            for n in range(1, instr.size):
                info.mark(addr + n, info.MARK_INSTR | info.MARK_DATA)

            target = instr.jumpTarget(active_bank)
            if target:
                if instr.type == instruction.JR:
                    info.addRomSymbol(target, addr)
                else:
                    info.addRomSymbol(target)
                todo.append(target)

            if instr.type == instruction.RST and instr.p0 == args.rstJumpTable:
                addr += 1
                while True:
                    if info.hasMark(addr, info.MARK_INSTR):
                        break
                    target = struct.unpack("<H", rom.data[addr:addr + 2])[0]
                    if 0x4000 <= target < 0x8000:
                        target = (target & 0x3FFF) | (addr & 0xFFFFC000)
                    info.mark(addr, info.MARK_DATA | info.MARK_PTR_LOW)
                    info.mark(addr + 1, info.MARK_DATA | info.MARK_PTR_HIGH)
                    info.mark(target, info.MARK_INSTR)
                    todo.append(target)
                    addr += 2
                break

            if not instr.hasNext():
                break
            addr += instr.size

    info.updateSymbols()
    # info.dumpStats()

    def out(addr, size, data):
        print("    %-30s ; $%04x" % (data, addr))

    addr = 0
    info.printRegs()
    print("""
ld_long_load: MACRO
    db $FA
    dw \\1
ENDM
ld_long_store: MACRO
    db $EA
    dw \\1
ENDM
""")
    for bank in range(len(rom.data) // 0x4000):
        print("")
        if bank == 0:
            print("SECTION \"bank00\", ROM0[$0000]")
        else:
            print("SECTION \"bank%02x\", ROMX[$4000], BANK[$%02x]" % (bank, bank))
        addr = 0x4000 * bank
        end_of_bank = addr + 0x4000
        while addr < end_of_bank:
            if addr in info.rom_symbols:
                if not info.rom_symbols[addr].startswith("."):
                    print("")
                print("%s:" % (info.rom_symbols[addr]))
            if info.hasMark(addr, info.MARK_INSTR):
                instr = Instruction(rom, addr)
                out(addr, instr.size, instr.format(info))
                addr += instr.size
            else:
                size = 1
                while size < 8 and addr + size < end_of_bank and addr + size not in info.rom_symbols and not info.hasMark(addr + size, info.MARK_INSTR):
                    size += 1
                if info.hasMark(addr - 1, info.MARK_INSTR) and not any(rom.data[addr:addr+size]):
                    while addr + size < end_of_bank and not info.hasMark(addr + size, info.MARK_INSTR) and rom.data[addr+size] == 0 and addr + size not in info.rom_symbols:
                        size += 1
                    out(addr, size, "ds   %d" % (size))
                else:
                    out(addr, size, "db   " + ", ".join(map(lambda n: "$%02x" % (n), rom.data[addr:addr+size])))
                addr += size
