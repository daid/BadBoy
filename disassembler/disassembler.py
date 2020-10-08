import os
import shutil

from romInfo import RomInfo
from assemblyFile import AssemblyFile
from block.header import ROMHeader
from block.code import CodeBlock
from block.gfx import GfxBlock
from sourceReader import SourceReader
from annotation.annotation import callAnnotation
from autoLabel import AutoLabelLocalizer
from annotation.simple import DataBlock


class Disassembler:
    def __init__(self, rom):
        self.__rom = rom
        RomInfo.init(rom)

    def readSources(self, path):
        if os.path.exists(os.path.join(path, "src")):
            for filename in os.listdir(os.path.join(path, "src")):
                if not filename.endswith(".asm"):
                    continue
                
                SourceReader(path).readFile(os.path.join("src", filename))

    def processRom(self):
        # First process all the annotations
        for bank in RomInfo.getRomBanks():
            for addr, comments in bank.getAllComments():
                for comment in comments:
                    if comment.startswith("@"):
                        callAnnotation(bank, addr, comment[1:])
            for addr, comment in bank.getAllInlineComments():
                if comment.startswith("@"):
                    callAnnotation(bank, addr, comment[1:])

        # Next process our normal entry point, header info and interrupts.
        ROMHeader(RomInfo.romBank(0))
        if RomInfo.romBank(0)[0x0100] is None:
            CodeBlock(RomInfo.romBank(0), 0x0100).addLabel(0x0100, "entry")

        for addr, name in [(0x0040, "isrVBlank"), (0x0048, "isrLCDC"), (0x0050, "isrTimer"), (0x0058, "isrSerial"), (0x0060, "isrJoypad")]:
            if RomInfo.memoryAt(addr).byte(addr) not in (0x00, 0xff) and RomInfo.memoryAt(addr)[addr] == None:
                CodeBlock(RomInfo.romBank(0), addr).addLabel(addr, name)

        # Finally, for any data that has no blocks on it, see if we have marks from instrumentation that can decode it
        for bank in RomInfo.getRomBanks():
            for addr in range(bank.base_address, bank.base_address + len(bank)):
                if not bank[addr]:
                    if bank.hasMark(addr, "CODE"):
                        CodeBlock(bank, addr)
                    elif bank.hasMark(addr, "GFX_LOW") and bank.hasMark(addr + 1, "GFX_HIGH"):
                        size = 2
                        while size < 16 and bank.hasMark(addr + size, "GFX_LOW") and bank.hasMark(addr + size + 1, "GFX_HIGH"):
                            size += 2
                        GfxBlock(bank, addr, bpp=2, size=size//2)
                    elif bank.hasMark(addr, "GFX_HIGH"):
                        size = 1
                        while size < 8 and bank.hasMark(addr + size, "GFX_HIGH"):
                            size += 1
                        GfxBlock(bank, addr, bpp=1, size=size)
                    elif bank.hasMark(addr, "PTR_LOW") and bank.hasMark(addr + 1, "PTR_HIGH"):
                        DataBlock(bank, addr, format="p", amount=1)
                    elif bank.hasMark(addr, "WORD_LOW") and bank.hasMark(addr + 1, "WORD_HIGH"):
                        DataBlock(bank, addr, format="w", amount=1)

    def export(self, path):
        for bank in RomInfo.getRomBanks():
            AutoLabelLocalizer(bank)

        if not os.path.exists(path):
            shutil.copytree(os.path.join(os.path.dirname(__file__), "template"), path)
        open(os.path.join(path, "rom.gb.md5"), "wt").write("%s rom.gb\n" % (self.__rom.md5sum()))

        objfiles = []
        for bank in RomInfo.getRomBanks():
            print("Processing bank: %d" % (bank.bankNumber))
            self.__exportRomBank(AssemblyFile(os.path.join(path, "src", "bank%02X.asm" % (bank.bankNumber)), bank), bank)
        
        f = AssemblyFile(os.path.join(path, "src", "memory.asm"))
        self.__exportRam(f, RomInfo.getWRam())
        self.__exportRam(f, RomInfo.getHRam())
        
        macro_file = open(os.path.join(path, "src", "include", "macros.inc"), "wt")
        for macro, contents in sorted(RomInfo.macros.items()):
            macro_file.write("%s: MACRO\n" % (macro))
            for line in contents.rstrip().split("\n"):
                macro_file.write("    %s\n" % (line.rstrip()))
            macro_file.write("ENDM\n")

        charmap_file = open(os.path.join(path, "src", "include", "charmaps.inc"), "wt")
        for name, data in sorted(RomInfo.charmap.items()):
            if name == "main":
                charmap_file.write("SETCHARMAP %s\n" % (name))
            else:
                charmap_file.write("NEWCHARMAP %s\n" % (name))
            for key, value in sorted(data.items()):
                charmap_file.write("CHARMAP \"%s\", %d\n" % (value, key))

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

    def __exportRam(self, file, memory):
        file.start(memory)
        memory_end = memory.base_address + len(memory)
        while file.addr < memory_end:
            size = 1
            while file.addr + size < memory_end and not memory.getLabel(file.addr + size):
                size += 1
            file.asmLine(size, "ds %d" % (size), is_data=True)
