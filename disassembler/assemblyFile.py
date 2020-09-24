import os


class AssemblyFile:
    def __init__(self, filename, memory):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.__file = open(filename, "wt")
        self.__file.write(";; Disassembled with BadBoy Disassembler: https://github.com/daid/BadBoy\n\n")
        self.__file.write("INCLUDE \"include/hardware.inc\"\n")
        self.__file.write("INCLUDE \"include/macros.inc\"\n")
        if memory.bankNumber == 0:
            self.__file.write("SECTION \"bank00\", ROM0[$0000]\n")
        else:
            self.__file.write("SECTION \"bank%02x\", ROMX[$4000], BANK[$%02x]\n" % (memory.bankNumber, memory.bankNumber))
        self.addr = memory.base_address
        self.__memory = memory
    
    def label(self, label):
        label = str(label)
        if not label.startswith("."):
            self.__file.write("\n")
        self.__file.write("%s:\n" % (label))
    
    def asmLine(self, size, code, *args, is_data=False):
        label = self.__memory.getLabel(self.addr)
        if label:
            self.label(label)
    
        if args:
            code = "%-4s %s" % (code, ", ".join(args))
        self.__file.write("    %-50s ;; %02x:%04x" % (code, self.__memory.bankNumber, self.addr))
        if is_data:
            pass
            #output.write(" ")
            #for n in range(size):
            #    output.write(self.info.classifyDataAsChar(address+n))
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
