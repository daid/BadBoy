import os
from memory.rom import RomMemory
from memory.ram import WRamMemory


class AssemblyFile:
    def __init__(self, filename, memory=None, *, addr=None):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.__file = open(filename, "wt")
        self.__file.write(";; Disassembled with BadBoy Disassembler: https://github.com/daid/BadBoy\n")
        self.__file.write("\n")
        if addr is None:
            self.__file.write("INCLUDE \"include/hardware.inc\"\n")
            self.__file.write("INCLUDE \"include/macros.inc\"\n")
            self.__file.write("INCLUDE \"include/charmaps.inc\"\n")
        self.addr = None
        self.__memory = None
        self.__addr_prefix = None
        self.__last_label = "NONE"

        if memory:
            self.start(memory, addr)

    def start(self, memory, addr=None):
        self.__file.write("\n")
        if isinstance(memory, RomMemory):
            if addr is None:
                if memory.bankNumber == 0:
                    self.__file.write("SECTION \"bank00\", ROM0[$0000]\n")
                else:
                    self.__file.write("SECTION \"bank%02x\", ROMX[$4000], BANK[$%02x]\n" % (memory.bankNumber, memory.bankNumber))
            self.__addr_prefix = "%02x:" % (memory.bankNumber)
        else:
            if addr is None:
                self.__file.write("SECTION \"%s\", %s[$%04x]\n" % (memory.type.lower(), memory.type.upper(), memory.base_address))
            self.__addr_prefix = ""

        if addr is None:
            self.addr = memory.base_address
        else:
            self.addr = addr
        self.__memory = memory

    def newline(self):
        self.__file.write("\n")

    def comment(self, line):
        self.__file.write("    ;;%s\n" % (line))
    
    def label(self, label):
        if not label.startswith("."):
            self.__last_label = label
        self.__file.write("%s:\n" % (label))

    def include(self, filename):
        self.__file.write('INCLUDE "%s"\n' % (filename))

    def asmLine(self, size, code, *args, is_data=False, add_data_comment=True):
        if args:
            code = "%-4s %s" % (code, ", ".join(args))

        label = self.__memory.getLabel(self.addr)
        if label:
            label = str(label)
            if "." in label and self.__last_label.split(".")[0] == label.split(".")[0]:
                label = "." + label.split(".", 1)[1]
            if not label.startswith("."):
                self.__file.write("\n")
        comments = self.__memory.getComments(self.addr)
        if comments:
            for comment in comments:
                self.__file.write(";%s\n" % (comment))
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
                    if self.__memory.hasMark(self.addr+n, "DATA"):
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
        self.__file.write("\n")
        self.addr += size

    def dataLine(self, size):
        self.asmLine(size, "db   " + ", ".join(map(lambda n: "$%02x" % (n), self.__memory.data(self.addr, size))), is_data=True)
