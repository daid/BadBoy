import re
from annotation.annotation import annotation
from block.base import Block
from block.code import CodeBlock
from block.gfx import GfxBlock
from romInfo import RomInfo


@annotation
def code(memory, addr):
    CodeBlock(memory, addr)

@annotation
def data(memory, addr, *, format, amount=1):
    DataBlock(memory, addr, format=format, amount=int(amount) if amount is not None else None);

@annotation
def jumptable(memory, addr, *, amount=None, label=None):
    JumpTable(memory, addr, amount=int(amount) if amount is not None else None)

@annotation
def bank(memory, addr, bank_nr):
    memory.setActiveRomBankAt(addr, int(bank_nr))

@annotation
def string(memory, addr, *, size=None):
    StringBlock(memory, addr, size=int(size) if size is not None else None)

@annotation
def gfx(memory, addr):
    GfxBlock(memory, addr, bpp=2, size=8)

@annotation
def jumptablefunction(memory, addr):
    JumpTableFunction(memory, addr)

class JumpTableFunction(CodeBlock):
    def onCall(self, from_memory, from_address, next_addr):
        JumpTable(from_memory, next_addr)

class DataBlock(Block):
    def __init__(self, memory, addr, *, format, amount):
        super().__init__(memory, addr)
        self.__format = format
        self.__amount = amount
        self.__code = "data_%s" % (format)

        if re.match(r"b+$", format):
            self.__code = "db"
        elif re.match(r"[wp]+$", format):
            self.__code = "dw"
        else:
            macro = []
            for idx, f in enumerate(format.lower()):
                if f == "b":
                    macro.append("db \\1")
                elif f in ("w", "p"):
                    macro.append("dw \\1")
                macro.append("shift")
            RomInfo.macros[self.__code] = "\n".join(macro)


        for n in range(amount):
            size = 0
            for f in format.lower():
                if f == "b":
                    size += 1
                elif f == "w":
                    size += 2
                elif f == "p":
                    target = self.memory.word(addr + len(self) + size)
                    if target >= memory.base_address and target < memory.base_address + len(memory):
                        memory.addAutoLabel(target, addr, "data")
                    size += 2
            self.resize(len(self) + size)

    def export(self, file):
        for n in range(self.__amount):
            size = 0
            params = []
            for f in self.__format.lower():
                if f == "b":
                    params.append("$%02x" % self.memory.byte(file.addr + size))
                    size += 1
                elif f == "w":
                    params.append("$%04x" % self.memory.word(file.addr + size))
                    size += 2
                elif f == "p":
                    label = self.memory.getLabel(self.memory.word(file.addr + size))
                    if label:
                        label = str(label)
                    else:
                        label = "$%04x" % self.memory.word(file.addr + size)
                    params.append(label)
                    size += 2
            file.asmLine(size, self.__code, *params, is_data=True)


class JumpTable(Block):
    def __init__(self, memory, addr, *, amount=None):
        super().__init__(memory, addr)

        for n in range(amount if amount is not None else 0x2000):
            target = memory.word(addr + len(self))
            if target >= memory.base_address and target < memory.base_address + len(memory):
                CodeBlock(memory, target)
                memory.addAutoLabel(target, addr, "call")
            if not self.resize(len(self) + 2, allow_fail=amount is None):
                break

    def export(self, file):
        for n in range(len(self) // 2):
            label = self.memory.getLabel(self.memory.word(file.addr))
            if label:
                label = str(label)
            else:
                label = "$%04x" % self.memory.word(file.addr)
            file.asmLine(2, "dw", label, is_data=True)


class StringBlock(Block):
    MAPPING = {
        0x09: r"\t",
        0x0A: r"\n",
        0x0D: r"\r",
        0x22: r"\"",
        0x5C: "\\",
        0x7B: r"\{",
        0x7D: r"\}",
    }

    def __init__(self, memory, addr, *, size=None):
        super().__init__(memory, addr)
        
        if size is None:
            size = 0
            while memory.byte(addr + size) != 0:
                size += 1
            size += 1
        self.resize(size)

    def export(self, file):
        s = ""
        in_string = False
        for n in range(len(self)):
            value = self.memory.byte(file.addr + n)
            if value in self.MAPPING:
                if not in_string:
                    s += "\""
                    in_string = True
                s += self.MAPPING[value]
            elif 32 <= value < 128:
                if not in_string:
                    s += "\""
                    in_string = True
                s += "%c" % (value)
            else:
                if in_string:
                    s += "\""
                    in_string = False
                s += ", $%02x" % (value)
        if in_string:
            s += "\""
        file.asmLine(len(self), "db", s, is_data=True)
