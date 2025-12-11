import binascii
import struct
import argparse


class BPS:
    def __init__(self, old, new, patch):
        self.old = open(old, "rb").read()
        self.new = open(new, "rb").read()
        self.patch = open(patch, "wb")
        self.patch = bytearray(b'BPS1')
        self.number(len(self.old))
        self.number(len(self.new))
        self.number(0)
        self.ptr = 0
        self.srcRelOff = 0
        self.dstRelOff = 0

        while self.ptr < len(self.new):
            unchanged_size = 0
            while self.ptr + unchanged_size < len(self.old) and self.old[self.ptr+unchanged_size] == self.new[self.ptr+unchanged_size]:
                unchanged_size += 1
            if unchanged_size > 0:
                self.number(0 | ((unchanged_size - 1) << 2))
                self.ptr += unchanged_size

            changed_size = 0
            while self.ptr + changed_size < len(self.new) and self.old[self.ptr+changed_size] != self.new[self.ptr+changed_size]:
                changed_size += 1
            if changed_size > 0:
                data = self.new[self.ptr:self.ptr+changed_size]
                old_pos = self.old.find(data)
                new_pos = self.new.find(data)
                if old_pos >= 0 and changed_size > 4:
                    self.number(2 | ((changed_size - 1) << 2))
                    self.signednumber(old_pos - self.srcRelOff)
                    self.srcRelOff = old_pos + changed_size
                elif new_pos < self.ptr and changed_size > 4:
                    self.number(3 | ((changed_size - 1) << 2))
                    self.signednumber(new_pos - self.dstRelOff)
                    self.dstRelOff = new_pos + changed_size
                else:
                    self.number(1 | ((changed_size - 1) << 2))
                    self.patch += self.new[self.ptr:self.ptr+changed_size]
                self.ptr += changed_size
        self.patch += struct.pack("<I", binascii.crc32(self.old))
        self.patch += struct.pack("<I", binascii.crc32(self.new))
        self.patch += struct.pack("<I", binascii.crc32(self.patch))
        open(patch, "wb").write(self.patch)

    def signednumber(self, value):
        if value < 0:
            self.number((-value << 1) | 1)
        else:
            self.number(value << 1)

    def number(self, value):
        assert value >= 0
        while True:
            x = value & 0x7F
            value >>= 7
            if value == 0:
                self.patch.append(0x80 | x)
                return
            self.patch.append(x)
            value -= 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("old_file")
    parser.add_argument("new_file")
    parser.add_argument("patch_file")
    args = parser.parse_args()
    BPS(args.old_file, args.new_file, args.patch_file)
