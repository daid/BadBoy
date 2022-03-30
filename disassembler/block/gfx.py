from .base import Block
import PIL.Image
import numpy
import os


def _to2bpp(value):
    return "`" + "".join("%d" % (((value >> n) & 0x01) | ((value >> (n + 7)) & 0x02)) for n in range(7, -1, -1))


class GfxBlock(Block):
    def __init__(self, memory, address, *, bpp=1, size=1):
        super().__init__(memory, address, size=bpp*size)
        
        self.bpp = bpp
        
        if bpp == 2:
            for n in range(1, len(self), 2):
                memory.ensureNoLabel(address + n)

    def export(self, file):
        for n in range(len(self) // self.bpp):
            if self.bpp == 1:
                file.asmLine(1, "db", "%{0:08b}".format(self.memory.byte(file.addr)))
            elif self.bpp == 2:
                file.asmLine(2, "dw", _to2bpp(self.memory.word(file.addr)))
        file.newline()


class GfxImageBlock(Block):
    def __init__(self, memory, address, *, name, width=16, height=16):
        super().__init__(memory, address, size=width*height*16)
        self.name = name
        self.width = width
        self.height = height

    def export(self, file):
        addr = file.addr
        img = numpy.zeros((self.height * 8, self.width * 8), dtype=numpy.uint8)
        for y in range(self.height):
            for x in range(self.width):
                for row in range(8):
                    a = self.memory.byte(addr)
                    b = self.memory.byte(addr + 1)
                    addr += 2
                    for col in range(8):
                        v = 0
                        if a & (0x80 >> col):
                            v |= 1
                        if b & (0x80 >> col):
                            v |= 2
                        img[y*8+row, x*8+col] = v
        img = PIL.Image.fromarray(img, "P")
        img.putpalette([0xc4,0xf0,0xc2, 0x5a,0xb9,0xa8, 0x1e,0x60,0x6e, 0x2d,0x1b,0x00])
        filename = os.path.join(file.basepath, "gfx", "%s.png" % (self.name))
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        img.save(filename)
        file.asmLine(len(self), "INCBIN", "\"%s.bin\"" % (self.name), add_data_comment=False)
