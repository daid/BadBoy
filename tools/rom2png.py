import argparse
import PIL.Image
import PIL.ImageDraw
import numpy

def oneBitPerPixel(data, width, height=None):
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
                    img[y*8+row, x*8+col] = v
    img = PIL.Image.fromarray(img, "P")
    img.putpalette([0xc4,0xf0,0xc2, 0x5a,0xb9,0xa8, 0x1e,0x60,0x6e, 0x2d,0x1b,0x00])
    return img

def twoBitsPerPixel(data, width, height=None):
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
                    img[y*8+row, x*8+col] = v
    img = PIL.Image.fromarray(img, "P")
    img.putpalette([0xc4,0xf0,0xc2, 0x5a,0xb9,0xa8, 0x1e,0x60,0x6e, 0x2d,0x1b,0x00])
    return img


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=str)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--1bpp", dest='one', action="store_true")
    args = parser.parse_args()

    data = open(args.rom, "rb").read()
    bank_count = len(data) // 0x4000
    
    rows = 512 * (2 if args.one else 1)
    img = PIL.Image.new("P", (bank_count * 136 + 64, rows + 32))
    draw = PIL.ImageDraw.Draw(img)
    img.putpalette([0xc4,0xf0,0xc2, 0x5a,0xb9,0xa8, 0x1e,0x60,0x6e, 0x2d,0x1b,0x00, 0x00,0x00,0x00, 0xFF,0xFF,0xFF])
    draw.rectangle(((0,0), img.size), 4)
    for addr in range(0, 0x4001, 0x0400):
        y = addr * rows // 0x4000 + 16
        draw.text((3, y - 10), "%04X" % (addr + 0x4000), 5)
        draw.text((bank_count * 136 + 32, y - 10), "%04X" % (addr + 0x4000), 5)
        draw.line((0, y, img.size[0], y), 5)
    for bank_nr in range(bank_count):
        draw.text((64 + 16 + bank_nr * 136, 0), "Bank%02X" % (bank_nr), 5)
        draw.text((64 + 16 + bank_nr * 136, rows + 16), "Bank%02X" % (bank_nr), 5)
        if args.one:
            img.paste(oneBitPerPixel(data[bank_nr*0x4000:bank_nr*0x4000+0x4000], 16), (32 + bank_nr * 136, 16))
        else:
            img.paste(twoBitsPerPixel(data[bank_nr*0x4000:bank_nr*0x4000+0x4000], 16), (32 + bank_nr * 136, 16))
    img.save(args.output)
