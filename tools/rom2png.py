import argparse
import PIL.Image
import PIL.ImageDraw
import numpy
import struct


ID_MASK = (0xFF << 32)
ID_ROM = (0x00 << 32)
ID_VRAM = (0x01 << 32)
ID_SRAM = (0x02 << 32)
ID_WRAM = (0x03 << 32)
ID_OAM = (0x04 << 32)
ID_IO = (0x05 << 32)
ID_HRAM = (0x06 << 32)
MARK_MASK = (0xFF << 40)
MARK_INSTR = (0x01 << 40)
MARK_DATA = (0x02 << 40)
MARK_PTR_LOW = (0x04 << 40)
MARK_PTR_HIGH = (0x08 << 40)
MARK_WORD_LOW = (0x10 << 40)
MARK_WORD_HIGH = (0x20 << 40)
MARK_BANK_SHIFT = (48)
MARK_BANK_MASK = (0xFFF << 48)

palette = [
    0xc4,0xf0,0xc2, 0x5a,0xb9,0xa8, 0x1e,0x60,0x6e, 0x2d,0x1b,0x00,
    0xC8,0x70,0x20, 0x20,0xB0,0x48, 0x08,0x48,0x28, 0x00,0x00,0x00,
    0xF8,0xF8,0x88, 0x60,0xB8,0x20, 0x30,0x68,0x28, 0x00,0x00,0x00,
    0xA0,0xF8,0xF8, 0x60,0xB8,0x20, 0x68,0x00,0xE8, 0x00,0x00,0x00,
]
palette += [n // 2 for n in palette]
palette += [
    0x00,0x00,0x00, 0xFF,0xFF,0xFF
]


def oneBitPerPixel(data, data_type, width, height=None):
    if height is None:
        height = len(data) // 8 // width
    addr = 0
    img = numpy.zeros((height * 8, width * 8), dtype=numpy.uint8)
    for y in range(height):
        for x in range(width):
            for row in range(8):
                a = data[addr]
                addr += 1
                for col in range(8):
                    v = 0
                    if a & (0x80 >> col):
                        v |= 3
                    img[y*8+row, x*8+col] = v + data_type[addr-2] * 4
    img = PIL.Image.fromarray(img, "P")
    img.putpalette(palette)
    return img

def twoBitsPerPixel(data, data_type, width, height=None):
    if height is None:
        height = len(data) // 16 // width
    addr = 0
    img = numpy.zeros((height * 8, width * 8), dtype=numpy.uint8)
    for y in range(height):
        for x in range(width):
            for row in range(8):
                a = data[addr]
                b = data[addr + 1]
                addr += 2
                for col in range(8):
                    v = 0
                    if a & (0x80 >> col):
                        v |= 1
                    if b & (0x80 >> col):
                        v |= 2
                    img[y*8+row, x*8+col] = v + data_type[addr-2] * 4
    img = PIL.Image.fromarray(img, "P")
    img.putpalette(palette)
    return img


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=str)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--1bpp", dest='one', action="store_true")
    parser.add_argument("--instrumentation", action='append', default=[])
    parser.add_argument("--diff", type=str, required=False)
    args = parser.parse_args()

    data = open(args.rom, "rb").read()
    bank_count = len(data) // 0x4000
    data_type = bytearray(len(data))
    for filename in args.instrumentation:
        f = open(filename, "rb")
        while True:
            record = f.read(16)
            if not record:
                break
            source, used_as = struct.unpack("<QQ", record)
            if (source & ID_MASK) == ID_ROM:
                if used_as & MARK_INSTR:
                    data_type[source & 0xFFFFFFFF] = 1
                if used_as & MARK_DATA:
                    data_type[source & 0xFFFFFFFF] = 2

    if args.diff:
        diff = open(args.diff, "rb").read()
        for n in range(min(len(data), len(diff))):
            if data[n] == diff[n]:
                data_type[n] |= 4

    pixels_per_bank = 512 * (2 if args.one else 1)
    rows = 1
    while ((bank_count + rows - 1) // rows) > rows * 4:
        rows += 1
    cols = (bank_count + rows - 1) // rows
    img = PIL.Image.new("P", (cols * 136 + 64, rows * (pixels_per_bank + 32)))
    draw = PIL.ImageDraw.Draw(img)
    img.putpalette(palette)
    draw.rectangle(((0,0), img.size), 32)
    for addr in range(0, 0x4001, 0x0400):
        for row in range(rows):
            y = addr * pixels_per_bank // 0x4000 + 16 + row * (pixels_per_bank + 32)
            draw.text((3, y - 10), "%04X" % (addr + 0x4000), 33)
            draw.text((cols * 136 + 32, y - 10), "%04X" % (addr + 0x4000), 33)
            draw.line((0, y, img.size[0], y), 17)
    for bank_nr in range(bank_count):
        x = 32 + (bank_nr % cols) * 136
        y = 16 + (bank_nr // cols) * (pixels_per_bank + 32)
        draw.text((32 + 16 + x, y - 16), "Bank%02X" % (bank_nr), 33)
        draw.text((32 + 16 + x, y + pixels_per_bank), "Bank%02X" % (bank_nr), 33)
        bank_data = data[bank_nr*0x4000:bank_nr*0x4000+0x4000]
        bank_type_data = data_type[bank_nr*0x4000:bank_nr*0x4000+0x4000]
        if args.one:
            img.paste(oneBitPerPixel(bank_data, bank_type_data, 16), (x, y))
        else:
            img.paste(twoBitsPerPixel(bank_data, bank_type_data, 16), (x, y))
    img.save(args.output)
