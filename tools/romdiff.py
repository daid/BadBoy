import sys
import os
import re
import bisect


def read_sym_file(filename):
    if not os.path.exists(filename):
        return []
    result = []
    for line in open(filename, "rt"):
        line = line.strip()
        m = re.match("([0-9a-fA-F]+):([0-9a-fA-F]+) (.+)", line)
        if m:
            bank = int(m.group(1), 16)
            addr = int(m.group(2), 16)
            label = m.group(3)
            if addr < 0x8000:
                result.append((bank * 0x4000 + (addr & 0x3FFF), label))
    result.sort()
    return result

if __name__ == "__main__":
    a = open(sys.argv[1], "rb").read()
    b = open(sys.argv[2], "rb").read()
    symbols_a = read_sym_file(os.path.splitext(sys.argv[1])[0] + ".sym")
    symbols_b = read_sym_file(os.path.splitext(sys.argv[2])[0] + ".sym")

    for n in range(len(a)):
        if a[n] != b[n] and (n > 0x150 or n < 0x100):
            bank = n // 0x4000
            addr = n & 0x3FFF
            if bank > 0:
                addr += 0x4000
            symbol = None
            idx = bisect.bisect_right(symbols_a, n, key=lambda s: s[0])
            if idx < len(symbols_a):
                s = f"  {symbols_a[idx-1][1]}+{n-symbols_a[idx-1][0]}"
            else:
                s = ""
            idx = bisect.bisect_right(symbols_b, n, key=lambda s: s[0])
            if idx < len(symbols_b):
                s += f"  {symbols_b[idx-1][1]}+{n-symbols_b[idx-1][0]}"
            else:
                s += ""
            print("%02x:%04x: %02x != %02x%s" % (bank, addr, a[n], b[n], s))
