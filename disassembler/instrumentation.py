import struct

from romInfo import RomInfo


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


def processInstrumentation(filename):
    f = open(filename, "rb")
    while True:
        data = f.read(16)
        if not data:
            break
        source, used_as = struct.unpack("<QQ", data)
        if (source & ID_MASK) == ID_ROM:
            addr = source & 0x3FFF
            bank = (source >> 14) & 0x3FF
            if bank > 0:
                addr |= 0x4000
            
            memory = RomInfo.romBank(bank)
            if used_as & MARK_INSTR:
                memory.mark(addr, "CODE")
            if used_as & MARK_DATA:
                memory.mark(addr, "DATA")
                used_as_id = (used_as & ID_MASK)
                used_as_addr = (used_as & 0xFFFF)
                if used_as_id == ID_VRAM:
                    if used_as_addr < 0x1800:
                        if (used_as_addr & 1) == 0:
                            memory.mark(addr, "GFX_LOW")
                        else:
                            memory.mark(addr, "GFX_HIGH")
                    else:
                        memory.mark(addr, "TILE")
                elif used_as_id == ID_OAM:
                    pass
                elif used_as_id == ID_IO:
                    pass
                elif used_as_id == ID_ROM:
                    if used_as_addr & 0xF000 == 0x2000:
                        memory.mark(addr, "BANK")
            if used_as & MARK_PTR_LOW:
                memory.mark(addr, "PTR_LOW")
            if used_as & MARK_PTR_HIGH:
                memory.mark(addr, "PTR_HIGH")
            if used_as & MARK_WORD_LOW:
                memory.mark(addr, "WORD_LOW")
            if used_as & MARK_WORD_HIGH:
                memory.mark(addr, "WORD_HIGH")

            if bank == 0 and (used_as & MARK_BANK_MASK) != 0 and (used_as & MARK_BANK_MASK) >> MARK_BANK_SHIFT:
                memory.setActiveRomBankAt(addr, (used_as & MARK_BANK_MASK) >> MARK_BANK_SHIFT)
