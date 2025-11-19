import argparse

def find_all(rom, search):
    result = []
    start = 0
    while True:
        idx = rom.find(search, start)
        if idx == -1:
            return result
        start = idx + 1
        result.append(idx)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rom")
    parser.add_argument("search", nargs='+')
    args = parser.parse_args()
    rom = open(args.rom, "rb").read()
    for n in range(-128, 128):
        results = []
        for search in args.search:
            s = bytes([(ord(c) + n + 256) & 0xFF for c in search])
            results.append(find_all(rom, s))
        if all(results):
            print(f"Found the strings at character shift {n}")
            for res, search in zip(results, args.search):
                print(f"{search}:")
                for offset in res:
                    bank = offset // 0x4000
                    offset &= 0x3FFF
                    if bank:
                        offset += 0x4000
                    print(f"  at: {bank:02x}:{offset:04x}")


if __name__ == "__main__":
    main()
