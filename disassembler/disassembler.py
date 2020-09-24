import os
import shutil

from romInfo import RomMemoryMapping
from assemblyFile import AssemblyFile
from block.header import ROMHeader
from block.code import CodeBlock


class Disassembler:
    def __init__(self, rom):
        self.__rom = rom
        self.__mapping = RomMemoryMapping(rom)

        ROMHeader(self.__mapping.romBank(0))
        CodeBlock(self.__mapping.romBank(0), 0x0100).addLabel(0x0100, "entry")
        
        for addr, name in [(0x0040, "isrVBlank"), (0x0048, "isrLCDC"), (0x0050, "isrTimer"), (0x0058, "isrSerial"), (0x0060, "isrJoypad")]:
            if self.__mapping.memoryAt(addr).byte(addr) != 0 and self.__mapping.memoryAt(addr)[addr] == None:
                CodeBlock(self.__mapping.romBank(0), addr).addLabel(addr, name)

    def export(self, path):
        if not os.path.exists(path):
            shutil.copytree(os.path.join(os.path.dirname(__file__), "template"), path)
            open(os.path.join(path, "rom.gb.md5"), "wt").write("%s rom.gb\n" % (self.__rom.md5sum()))

        objfiles = []
        for bank in self.__mapping.getRomBanks():
            print("Processing bank: %d" % (bank.bankNumber))
            self.__exportRomBank(AssemblyFile(os.path.join(path, "src", "bank%02x.asm" % (bank.bankNumber)), bank), bank)
        
        macros = {
            "ld_long_load": "db $FA\ndw \\1",
            "ld_long_store": "db $EA\ndw \\1",
            "short_halt": "db $76",
            "short_stop": "db $10",
        }
        macro_file = open(os.path.join(path, "src", "include", "macros.inc"), "wt")
        for macro, contents in sorted(macros.items()):
            macro_file.write("%s: MACRO\n" % (macro))
            for line in contents.rstrip().split("\n"):
                macro_file.write("    %s\n" % (line.rstrip()))
            macro_file.write("ENDM\n")

    def __exportRomBank(self, file, bank):
        bank_len = len(bank)
        bank_end = bank.base_address + bank_len
        while file.addr < bank_end:
            if bank[file.addr]:
                addr = file.addr
                bank[file.addr].export(file)
                assert addr + len(bank[addr]) == file.addr, "Block export of type %s failed to export proper size (%d != %d)" % (bank[addr].__class__.__name__, file.addr - addr, len(bank[addr]))
            else:
                size = 1
                while size < 8 and file.addr + size < bank_end and not bank[file.addr + size] and not bank.getLabel(file.addr + size):
                    size += 1
                file.dataLine(size)
