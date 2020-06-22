
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

class Instrumentation:
    def __init__(self, rom):
        self.rom = [0] * len(rom.data)

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
            if (source & ID_MASK) == ID_ROM:
                self.rom[source & 0xFFFFFFFF] = used_as
