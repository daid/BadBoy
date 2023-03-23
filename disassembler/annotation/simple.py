import re
from annotation.annotation import annotation
from block.base import Block
from block.code import CodeBlock
from block.gfx import GfxBlock, GfxImageBlock
from romInfo import RomInfo
from autoLabel import RelativeLabel


@annotation
def code(memory, addr):
    CodeBlock(memory, addr)

@annotation
def data(memory, addr, *, format, amount=1):
    DataBlock(memory, addr, format=format, amount=int(amount) if amount is not None else None);

@annotation
def jumptable(memory, addr, *, amount=None, label=None):
    JumpTable(memory, addr, amount=int(amount) if amount is not None else None)

@annotation(priority=10)
def bank(memory, addr, bank_nr, size=1):
    for n in range(int(size)):
        memory.setActiveRomBankAt(addr + n, int(bank_nr))

@annotation
def string(memory, addr, *, size=None):
    StringBlock(memory, addr, size=int(size) if size is not None else None)

@annotation
def gfx(memory, addr):
    GfxBlock(memory, addr, bpp=2, size=8)

@annotation
def gfximg(memory, addr, name, width, height):
    width = int(width)
    height = int(height)
    GfxImageBlock(memory, addr, name=name, width=width, height=height)
    for n in range(16, width*height*16, 16):
        RelativeLabel(memory, addr + n, addr)

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
            if n == 0:
                for offset in range(1, size):
                    RelativeLabel(memory, addr + len(self) + offset, addr)
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
                    addr = self.memory.word(file.addr + size)
                    label = self.memory.getLabel(addr)
                    if label:
                        label = str(label)
                    elif addr >= 0x100:
                        label = RomInfo.getLabelAt(addr, RomInfo.romBank(self.memory.activeRomBankAt(file.addr + size)))
                        if not label:
                            label = "$%04x" % addr
                        else:
                            label = str(label)
                    else:
                        label = "$%04x" % addr
                    params.append(label)
                    size += 2
            file.asmLine(size, self.__code, *params, is_data=True, comment=("$%02x" % (n)) if self.__amount > 1 else None)


class JumpTable(Block):
    def __init__(self, memory, addr, *, amount=None):
        super().__init__(memory, addr)

        for n in range(amount if amount is not None else 0x2000):
            if not self.resize(len(self) + 2, allow_fail=amount is None):
                break
            target = memory.word(addr + len(self) - 2)
            if target >= memory.base_address and target < memory.base_address + len(memory) and target != 0x0000:
                CodeBlock(memory, target)
                memory.addAutoLabel(target, addr, "call")
            elif target >= 0x0100 and target < 0x4000:
                CodeBlock(RomInfo.romBank(0), target)
                RomInfo.romBank(0).addAutoLabel(target, addr, "call")

    def export(self, file):
        for n in range(len(self) // 2):
            addr = self.memory.word(file.addr)
            label = self.memory.getLabel(addr) if addr >= 0x4000 else RomInfo.romBank(0).getLabel(addr)
            if label:
                label = str(label)
            else:
                label = "$%04x" % self.memory.word(file.addr)
            file.asmLine(2, "dw", label, is_data=True, comment=("$%02x" % (n)))


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
