from .base import Memory


class RomMemory(Memory):
    def __init__(self, rom, bank):
        super().__init__("rom%x" % (bank), 0x4000, base_address=0x0000 if bank == 0 else 0x4000)
        self.__bank = bank
        self.__rom = rom

    @property
    def bankNumber(self):
        return self.__bank

    def data(self, addr, size):
        addr = addr - self.base_address + self.__bank * 0x4000
        return self.__rom[addr:addr+size]

    def byte(self, addr):
        addr = addr - self.base_address + self.__bank * 0x4000
        return self.__rom[addr]

    def word(self, addr):
        addr = addr - self.base_address + self.__bank * 0x4000
        return (self.__rom[addr]) | (self.__rom[addr + 1] << 8)
