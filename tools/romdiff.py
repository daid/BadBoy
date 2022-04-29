import sys

if __name__ == "__main__":
    a = open(sys.argv[1], "rb").read()
    b = open(sys.argv[2], "rb").read()
    for n in range(len(a)):
        if a[n] != b[n] and (n > 0x150 or n < 0x100):
            bank = n // 0x4000
            addr = n & 0x3FFF
            if bank > 0:
                addr += 0x4000
            print("%02x:%04x: %02x != %02x" % (bank, addr, a[n], b[n]))
