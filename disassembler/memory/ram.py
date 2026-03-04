from .base import Memory


class VRamMemory(Memory):
    def __init__(self):
        super().__init__("vram", 0x2000, base_address=0x8000)

    def addAutoLabel(self, addr, source, type):
        if self.getLabel(addr) == None:
            self.addLabel(addr, "v%04X" % (addr))

class SRamMemory(Memory):
    def __init__(self):
        super().__init__("sram", 0x2000, base_address=0xA000)

    def addAutoLabel(self, addr, source, type):
        if self.getLabel(addr) == None:
            self.addLabel(addr, "s%04X" % (addr))

class WRamMemory(Memory):
    def __init__(self):
        super().__init__("wram0", 0x2000, base_address=0xC000)

    def addAutoLabel(self, addr, source, type):
        if self.getLabel(addr) == None:
            self.addLabel(addr, "w%04X" % (addr))

class WRamMemoryBanked(Memory):
    def __init__(self, bank):
        super().__init__("wram0" if bank == 0 else "wramx", 0x1000, base_address=0xC000 if bank == 0 else 0xD000)
        self.__bank = bank

    @property
    def bankNumber(self):
        return self.__bank

    def addAutoLabel(self, addr, source, type):
        if self.getLabel(addr) == None:
            if self.__bank == 0:
                self.addLabel(addr, "w%04X" % (addr))
            else:
                self.addLabel(addr, "w%01X_%04X" % (self.__bank, addr))

class OAMMemory(Memory):
    def __init__(self):
        super().__init__("oam", 0x00A0, base_address=0xFE00)

    def addAutoLabel(self, addr, source, type):
        if self.getLabel(addr) == None:
            self.addLabel(addr, "oam%04X" % (addr))

class HRamMemory(Memory):
    def __init__(self):
        super().__init__("hram", 0x007F, base_address=0xFF80)

    def addAutoLabel(self, addr, source, type):
        if self.getLabel(addr) == None:
            self.addLabel(addr, "h%04X" % (addr))
