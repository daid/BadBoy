from .base import Memory


class RomMemory(Memory):
    def __init__(self, rom, bank):
        super().__init__("rom%x" % (bank), 0x4000, base_address=0x0000 if bank == 0 else 0x4000)
        self.__bank = bank
        self.__rom = rom
        self.__active_rom_bank_per_addr = {}
        self.main_filename = "src/bank%02X.asm" % (bank)

    @property
    def bankNumber(self):
        return self.__bank
    
    def activeRomBankAt(self, addr):
        if self.__bank > 0:
            return self.__bank
        return self.__active_rom_bank_per_addr.get(addr, None)

    def setActiveRomBankAt(self, addr, bank_nr):
        assert self.__bank == 0
        self.__active_rom_bank_per_addr[addr] = bank_nr

    def data(self, addr, size):
        addr = addr - self.base_address + self.__bank * 0x4000
        return self.__rom[addr:addr+size]

    def byte(self, addr):
        addr = addr - self.base_address + self.__bank * 0x4000
        return self.__rom[addr]

    def word(self, addr):
        addr = addr - self.base_address + self.__bank * 0x4000
        return (self.__rom[addr]) | (self.__rom[addr + 1] << 8)

    def wordBE(self, addr):
        addr = addr - self.base_address + self.__bank * 0x4000
        return (self.__rom[addr] << 8) | (self.__rom[addr + 1])
