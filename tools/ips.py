import argparse


class Patch:
    def __init__(self, start, size, type=0):
        self.start = start
        self.size = size
        self.type = type

    @property
    def end(self):
        return self.start + self.size
    @end.setter
    def end(self, value):
        self.size = value - self.start

    def copy(self):
        return Patch(self.start, self.size, self.type)

    def __repr__(self):
        return f"{self.start>>14:02x}:{self.start&0x3FFF|0x4000:04x}-{self.end>>14:02x}:{self.end&0x3FFF|0x4000:04x} {self.size} {self.type}"


def findRLESequences(data, min_size=20):
    rle = []
    prev = None
    length = 0
    for idx, b in enumerate(data):
        if b == prev:
            length += 1
        else:
            if length >= min_size:
                rle.append((idx - length, length))
            prev = b
            length = 1
    if length >= min_size:
        rle.append((len(data) - length, length))
    return rle


# Sloppy IPS patch generator
def makePatch(old, new, patch):
    old = open(old, "rb").read()
    new = open(new, "rb").read()
    start = 0
    patches = []
    while start < len(new):
        if old[start] != new[start]:
            end = start
            while end < len(new) and old[end] != new[end]:
                end += 1
            size = end - start
            patches.append(Patch(start, size))
            start = end
        else:
            start += 1

    # Merge patches that are close enough to gether to save record space
    idx = 0
    while idx < len(patches) - 1:
        if patches[idx].end >= patches[idx+1].start - 4:
            size = patches[idx+1].end - patches[idx].start
            patches[idx] = Patch(patches[idx].start, size)
            patches.pop(idx+1)
        else:
            idx += 1
    # Find RLE patches
    idx = 0
    while idx < len(patches):
        p = patches[idx]
        result = [p.copy()]
        for offset, length in findRLESequences(new[p.start:p.end]):
            new_patch = Patch(p.start + offset, length)
            new_patch.type = 1
            if result[-1].start == new_patch.start:
                result.pop()
            else:
                result[-1].end = new_patch.start
            result.append(new_patch)
            if new_patch.end < p.end:
                result.append(Patch(new_patch.end, p.end - new_patch.end))
        patches[idx:idx+1] = result
        idx += len(result)

    patch = open(patch, "wb")
    patch.write(b"PATCH")
    for p in patches:
        patch.write(bytes([p.start >> 16, (p.start >> 8) & 0xFF, p.start & 0xFF]))
        if p.type == 0:
            patch.write(bytes([p.size >> 8, p.size & 0xFF]))
            patch.write(new[p.start:p.end])
        elif p.type == 1:
            patch.write(b'\x00\x00')
            patch.write(bytes([p.size >> 8, p.size & 0xFF, new[p.start]]))
    patch.write(b"EOF")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("old_file")
    parser.add_argument("new_file")
    parser.add_argument("patch_file")
    args = parser.parse_args()
    makePatch(args.old_file, args.new_file, args.patch_file)
