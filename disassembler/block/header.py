from .base import Block


class ROMHeader(Block):
    def __init__(self, memory):
        super().__init__(memory, 0x0104, size=0x0150 - 0x0104)

    def export(self, file):
        file.asmLine(16 * 3, "NINTENDO_LOGO", is_data=True)
        file.dataLine(15) # title
        file.dataLine(1) # gbc flag
        file.dataLine(2) # licensee code
        file.dataLine(1) # sgb flag
        file.dataLine(3) # cart type, rom size, ram size
        file.dataLine(3) # japan flag, old licensee code, rom version
        file.asmLine(3, "ds", "3", is_data=True)


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
