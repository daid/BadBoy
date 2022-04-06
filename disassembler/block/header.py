from .base import Block

CGB_FLAG = {0x00: "CART_COMPATIBLE_DMG", 0x80: "CART_COMPATIBLE_DMG_GBC", 0xC0: "CART_COMPATIBLE_GBC"}
SGB_FLAG = {0x00: "CART_INDICATOR_GB", 0x03: "CART_INDICATOR_SGB"}
CART_TYPE = {
    0x00: "CART_ROM",
    0x01: "CART_ROM_MBC1",
    0x02: "CART_ROM_MBC1_RAM",
    0x03: "CART_ROM_MBC1_RAM_BAT",
    0x05: "CART_ROM_MBC2",
    0x06: "CART_ROM_MBC2_BAT",
    0x08: "CART_ROM_RAM",
    0x09: "CART_ROM_RAM_BAT",
    0x0B: "CART_ROM_MMM01",
    0x0C: "CART_ROM_MMM01_RAM",
    0x0D: "CART_ROM_MMM01_RAM_BAT",
    0x0F: "CART_ROM_MBC3_BAT_RTC",
    0x10: "CART_ROM_MBC3_RAM_BAT_RTC",
    0x11: "CART_ROM_MBC3",
    0x12: "CART_ROM_MBC3_RAM",
    0x13: "CART_ROM_MBC3_RAM_BAT",
    0x19: "CART_ROM_MBC5",
    0x1A: "CART_ROM_MBC5_BAT",
    0x1B: "CART_ROM_MBC5_RAM_BAT",
    0x1C: "CART_ROM_MBC5_RUMBLE",
    0x1D: "CART_ROM_MBC5_RAM_RUMBLE",
    0x1E: "CART_ROM_MBC5_RAM_BAT_RUMBLE",
    0x22: "CART_ROM_MBC7_RAM_BAT_GYRO",
    0xFC: "CART_ROM_POCKET_CAMERA",
    0xFD: "CART_ROM_BANDAI_TAMA5",
    0xFE: "CART_ROM_HUDSON_HUC3",
    0xFF: "CART_ROM_HUDSON_HUC1",
}
ROM_SIZE = {
    0x00: "CART_ROM_32KB",
    0x01: "CART_ROM_64KB",
    0x02: "CART_ROM_128KB",
    0x03: "CART_ROM_256KB",
    0x04: "CART_ROM_512KB",
    0x05: "CART_ROM_1024KB",
    0x06: "CART_ROM_2048KB",
    0x07: "CART_ROM_4096KB",
    0x08: "CART_ROM_8192KB",
}
RAM_SIZE = {
    0x00: "CART_SRAM_NONE",
    0x01: "CART_SRAM_2KB",
    0x02: "CART_SRAM_8KB",
    0x03: "CART_SRAM_32KB",
    0x04: "CART_SRAM_128KB",
}
CART_DEST = {
    0x00: "CART_DEST_JAPANESE",
    0x01: "CART_DEST_NON_JAPANESE",
}

class ROMHeader(Block):
    def __init__(self, memory):
        super().__init__(memory, 0x0104, size=0x0150 - 0x0104)

    def export(self, file):
        file.asmLine(16 * 3, "ds", "$30", add_data_comment=False)
        ascii_title = ""
        while 32 <= self.memory.byte(file.addr + len(ascii_title)) < 128 and len(ascii_title) < 15:
            ascii_title += "%c" % (self.memory.byte(file.addr + len(ascii_title)))
        args = []
        if ascii_title:
            args.append("\"%s\"" % (ascii_title))
        args += ["$%02x" % self.memory.byte(file.addr + n) for n in range(len(ascii_title), 15)]
        file.asmLine(15, "db", *args, add_data_comment=False) # title
        file.asmLine(1, "db", self.lookup(CGB_FLAG, file.addr), add_data_comment=False) # gbc flag
        file.dataLine(2) # licensee code
        file.asmLine(1, "db", self.lookup(SGB_FLAG, file.addr), add_data_comment=False) # sgb flag
        file.asmLine(3, "db", self.lookup(CART_TYPE, file.addr), self.lookup(ROM_SIZE, file.addr + 1), self.lookup(RAM_SIZE, file.addr + 2), add_data_comment=False) # cart type, rom size, ram size
        file.asmLine(3, "db", self.lookup(CART_DEST, file.addr), "$%02x" % self.memory.byte(file.addr + 1), "$%02x" % self.memory.byte(file.addr + 2)) # japan flag, old licensee code, rom version
        file.asmLine(3, "ds", "3", is_data=True, add_data_comment=False)

    def lookup(self, table, addr=0):
        data = self.memory.byte(addr)
        return table.get(data, "$%02x" % (data))


# This block exports nothing. Should only be used at the end of sections!
class NoExport00(Block):
    def __init__(self, memory, end_addr):
        addr = end_addr - 1
        while memory.byte(addr) == 0x00 and memory.getLabel(addr) == None and memory[addr] == None:
            addr -= 1
        addr += 1
        super().__init__(memory, addr, size=end_addr-addr)

    def export(self, file):
        file.addr += len(self)
