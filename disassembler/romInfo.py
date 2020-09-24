from memory.rom import RomMemory
from memory.ram import VRamMemory
from memory.ram import ERamMemory
from memory.ram import WRamMemory
from memory.ram import HRamMemory
from memory.ram import OAMMemory
from memory.io import IOMemory
from memory.io import IERegMemory



class RomMemoryMapping:
    _instance = None

    def __init__(self, rom):
        RomMemoryMapping._instance = self

        self.__rom_banks = [RomMemory(rom, bank) for bank in range(rom.bankCount())]
        self.__vram = VRamMemory()
        self.__eram = ERamMemory()
        self.__wram = WRamMemory()
        self.__hram = HRamMemory()
        self.__oam = OAMMemory()
        self.__io = IOMemory()
        self.__ie = IERegMemory()

    def romBank(self, index):
        return self.__rom_banks[index]

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
            return self.__eram
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

    def getLabelAt(self, addr, active_rom_bank=None):
        memory = RomMemoryMapping._instance.memoryAt(addr, active_rom_bank)
        if not memory:
            return None
        block = memory[addr]
        if not block:
            return None
        return block.getLabel(addr)

    def getRomBanks(self):
        return self.__rom_banks
