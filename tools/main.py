from rom import ROM
from instruction import Instruction
import instruction
import struct
import PIL.Image


ID_MASK  = (0xFF << 32)
ID_ROM   = (0x00 << 32)
ID_VRAM  = (0x01 << 32)
ID_SRAM  = (0x02 << 32)
ID_WRAM  = (0x03 << 32)
ID_OAM   = (0x04 << 32)
ID_IO    = (0x05 << 32)
ID_HRAM  = (0x06 << 32)
MARK_MASK     = (0xFF << 40)
MARK_INSTR    = (0x01 << 40)
MARK_DATA     = (0x02 << 40)
MARK_PTR_LOW  = (0x04 << 40)
MARK_PTR_HIGH = (0x08 << 40)


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
    import sys
    rom = ROM(sys.argv[1])

    # f = open("tetris.data", "rb")
    # while True:
    #     data = f.read(16)
    #     if not data:
    #         break
    #     source, used_as = struct.unpack("<QQ", data)
    #     if (source & ID_MASK) == ID_ROM:
    #         if (used_as & MARK_INSTR):
    #             rom.mark(source & 0xFFFFFFF, rom.MARK_INSTR)
    #         if (used_as & MARK_DATA):
    #             rom.mark(source & 0xFFFFFFF, rom.MARK_DATA)
    #         if (used_as & ID_MASK) == ID_VRAM and (used_as & 0xFFFF) < 0x1800:
    #             rom.mark(source & 0xFFFFFFF, rom.MARK_TILE)
    #
    #     # if (source & ID_MASK) == ID_ROM and (used_as & MARK_DATA) and (used_as & ID_MASK) == ID_VRAM:
    #     #     print("%016x %016x %02x" % (source, used_as, rom.banks[(source >> 14) & 0xFF][source & 0x3FFF]))

    rom.dumpStats()

    done = set()
    todo = [0x0100, 0x0040, 0x0048, 0x0050, 0x0058, 0x0060]

    while todo:
        addr = todo.pop()

        while True:
            if addr in done or addr >= 0x4000:
                break
            done.add(addr)
            instr = Instruction(rom, addr)
            # print(hex(addr), instr)
            rom.mark(addr, rom.MARK_INSTR)
            for n in range(1, instr.size):
                rom.mark(addr, rom.MARK_INSTR | rom.MARK_DATA)

            target = instr.jumpTarget()
            if target and target < 0x8000:
                todo.append(target)

            if instr.type == instruction.RST and instr.value == 0x28:
                addr += 1
                while True:
                    if rom.hasMark(addr, rom.MARK_INSTR):
                        break
                    target = struct.unpack("<H", rom.data[(addr & 0x3FFF):(addr & 0x3FFF) + 2])[0]
                    rom.mark(addr, rom.MARK_DATA)
                    rom.mark(addr + 1, rom.MARK_DATA)
                    rom.mark(target, rom.MARK_INSTR)
                    todo.append(target)
                    addr += 2
                break

            if not instr.hasNext():
                break
            addr += instr.size

    rom.dumpStats()

    symbol_table = {}
    addr = 0
    while addr < 0x4000:
        if rom.hasMark(addr, rom.MARK_INSTR):
            instr = Instruction(rom, addr)
            print(hex(addr), instr.format(symbol_table))
            addr += instr.size
        else:
            print(hex(addr), "db $%02x" % (rom.data[addr]))
            addr += 1

    # exportAllAsGraphics(rom)
