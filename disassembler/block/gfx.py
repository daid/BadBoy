from .base import Block

def _to2bpp(value):
    return "`" + "".join("%d" % (((value >> n) & 0x01) | ((value >> (n + 7)) & 0x02)) for n in range(7, -1, -1))


class GfxBlock(Block):
    def __init__(self, memory, address, *, bpp=1, size=1):
        super().__init__(memory, address, size=bpp*size)
        
        self.bpp = bpp

    def export(self, file):
        for n in range(len(self) // self.bpp):
            if self.bpp == 1:
                file.asmLine(1, "db", "%{0:08b}".format(self.memory.byte(file.addr)))
            elif self.bpp == 2:
                file.asmLine(2, "dw", _to2bpp(self.memory.word(file.addr)))
        file.newline()
