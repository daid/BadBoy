import os
from memory.rom import RomMemory
from memory.ram import WRamMemory


class AssemblyFile:
    def __init__(self, basepath, filename, memory=None, *, addr=None):
        fullfilename = os.path.join(basepath, filename)
        os.makedirs(os.path.dirname(fullfilename), exist_ok=True)
        self.__file = open(fullfilename, "wt")
        self.__file.write(";; Disassembled with BadBoy Disassembler: https://github.com/daid/BadBoy\n")
        self.__file.write("\n")
        if addr is None:
            self.__file.write("INCLUDE \"include/hardware.inc\"\n")
            self.__file.write("INCLUDE \"include/macros.inc\"\n")
            self.__file.write("INCLUDE \"include/charmaps.inc\"\n")
            self.__file.write("INCLUDE \"include/constants.inc\"\n")
        self.addr = addr
        self.__memory = None
        self.__addr_prefix = None
        self.__last_label = "NONE"
        self.basepath = basepath
        if memory is not None:
            self.setMemory(memory)

    def setMemory(self, memory):
        self.__memory = memory
        if isinstance(self.__memory, RomMemory):
            self.__addr_prefix = "%02x:" % (self.__memory.bankNumber)
        else:
            self.__addr_prefix = ""

    def startSection(self, *, memory=None, addr=None, sectionname=None):
        if memory is not None:
            self.setMemory(memory)
        if addr is None:
            self.addr = self.__memory.base_address
        else:
            self.addr = addr

        self.__file.write("\n")
        if isinstance(self.__memory, RomMemory):
            if sectionname is None:
                sectionname = "bank%02x" % (self.__memory.bankNumber)
                if self.addr != self.__memory.base_address:
                    sectionname = "%s_%04x" % (sectionname, self.addr)
            if self.__memory.bankNumber == 0:
                self.__file.write("SECTION \"%s\", ROM0[$%04x]\n" % (sectionname, self.addr))
            else:
                self.__file.write("SECTION \"%s\", ROMX[$%04x], BANK[$%02x]\n" % (sectionname, self.addr, self.__memory.bankNumber))
            self.__addr_prefix = "%02x:" % (self.__memory.bankNumber)
        else:
            if addr is None:
                self.__file.write("SECTION \"%s\", %s[$%04x]\n" % (self.__memory.type.lower(), self.__memory.type.upper(), self.__memory.base_address))
            self.__addr_prefix = ""

    def newline(self):
        self.__file.write("\n")

    def comment(self, line):
        self.__file.write("    ;;%s\n" % (line))
    
    def label(self, label):
        if not label.startswith("."):
            self.__last_label = label
        self.__file.write("%s:\n" % (label))

    def include(self, filename):
        self.__file.write('\nINCLUDE "%s"\n' % (filename))

    def asmLine(self, size, code, *args, is_data=False, add_data_comment=True, comment=None):
        if args:
            code = "%-4s %s" % (code, ", ".join(args))

        section = self.__memory.getSectionStart(self.addr)
        if section is not None:
            self.startSection(addr=self.addr, sectionname=section)

        label = self.__memory.getLabel(self.addr)
        if label:
            label = str(label)
            if "." in label and self.__last_label.split(".")[0] == label.split(".")[0]:
                label = "." + label.split(".", 1)[1]
            if not label.startswith("."):
                self.__file.write("\n")
        comments = self.__memory.getComments(self.addr)
        if comments:
            for c in comments:
                self.__file.write(";%s\n" % (c))
        if label:
            self.label(label)

        inline_comment = self.__memory.getInlineComment(self.addr)
        if inline_comment:
            code = "%s ;%s" % (code,inline_comment)

        self.__file.write("    %-50s ;; %s%04x" % (code, self.__addr_prefix, self.addr))
        if isinstance(self.__memory, RomMemory) and add_data_comment:
            if is_data:
                self.__file.write(" ")
                for n in range(size):
                    if self.__memory.hasMark(self.addr+n, "PTR_LOW"):
                        self.__file.write("p")
                    elif self.__memory.hasMark(self.addr+n, "PTR_HIGH"):
                        self.__file.write("P")
                    elif self.__memory.hasMark(self.addr+n, "WORD_LOW"):
                        self.__file.write("w")
                    elif self.__memory.hasMark(self.addr+n, "WORD_HIGH"):
                        self.__file.write("W")
                    elif self.__memory.hasMark(self.addr+n, "DATA"):
                        self.__file.write(".")
                    else:
                        self.__file.write("?")
            else:
                for n in range(size):
                    self.__file.write(" $%02x" % (self.__memory.byte(self.addr+n)))
                #for n in range(size):
                #    s = self.info.classifyData(address+n)
                #    if s:
                #        output.write(" %s" % (s))
        if comment is not None:
            self.__file.write(" %s" % (comment))
        self.__file.write("\n")
        self.addr += size

    def dataLine(self, size):
        self.asmLine(size, "db   " + ", ".join(map(lambda n: "$%02x" % (n), self.__memory.data(self.addr, size))), is_data=True)
