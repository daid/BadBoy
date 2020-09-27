from annotation.annotation import annotation
from block.base import Block
from block.code import CodeBlock
from romInfo import RomInfo

@annotation
def code(memory, addr):
    CodeBlock(memory, addr)

@annotation
def data(memory, addr, *, format, amount=1):
    DataBlock(memory, addr, format=format, amount=int(amount) if amount is not None else None);

@annotation
def jumptable(memory, addr, *, amount=None):
    JumpTable(memory, addr, amount=int(amount))


class DataBlock(Block):
    def __init__(self, memory, addr, *, format, amount):
        super().__init__(memory, addr)
        self.__format = format
        self.__amount = amount

        macro = []
        for idx, f in enumerate(format.lower()):
            if f == "b":
                macro.append("db \%d" % (idx + 1))
            if f in ("w", "p"):
                macro.append("dw \%d" % (idx + 1))
        RomInfo.macros["data_%s" % (format)] = "\n".join(macro)


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
            file.asmLine(size, "data_%s" % (self.__format), *params, is_data=True)


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
            label = self.memory.getLabel(self.memory.word(file.addr + size))
            if label:
                label = str(label)
            else:
                label = "$%04x" % self.memory.word(file.addr + size)
            file.asmLine(2, "dw", label, is_data=True)
