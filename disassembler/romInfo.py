from memory.rom import RomMemory
from memory.ram import VRamMemory
from memory.ram import SRamMemory
from memory.ram import WRamMemory
from memory.ram import HRamMemory
from memory.ram import OAMMemory
from memory.io import IOMemory
from memory.io import IERegMemory



class RomInfo:
    @classmethod
    def init(self, rom):
        self.__rom_banks = [RomMemory(rom, bank) for bank in range(rom.bankCount())]
        self.__vram = VRamMemory()
        self.__sram = SRamMemory()
        self.__wram = WRamMemory()
        self.__hram = HRamMemory()
        self.__oam = OAMMemory()
        self.__io = IOMemory()
        self.__ie = IERegMemory()

    @classmethod
    def romBank(self, index):
        return self.__rom_banks[index]
    
    @classmethod
    def getWRam(self):
        return self.__wram

    @classmethod
    def getHRam(self):
        return self.__hram

    @classmethod
    def memoryAt(self, addr, active_rom_bank=None):
        if addr < 0x4000:
            return self.__rom_banks[0]
        if addr < 0x8000:
            if active_rom_bank and active_rom_bank.bankNumber == 0:
                return None
            return active_rom_bank
        if addr < 0xA000:
            return self.__vram
        if addr < 0xC000:
            return self.__sram
        if addr < 0xE000:
            return self.__wram
        if addr < 0xFE00:
            return None
        if addr < 0xFEA0:
            return self.__oam
        if addr < 0xFF00:
            return None
        if addr < 0xFF80:
            return self.__io
        if addr < 0xFFFF:
            return self.__hram
        if addr == 0xFFFF:
            return self.__ie
        return None

    @classmethod
    def getLabelAt(self, addr, active_rom_bank=None):
        memory = self.memoryAt(addr, active_rom_bank)
        if not memory:
            return None
        return memory.getLabel(addr)

    @classmethod
    def getRomBanks(self):
        return self.__rom_banks
