
class ROM:
    MARK_INSTR = 0x01
    MARK_DATA = 0x02
    MARK_TILE = 0x10
    MARK_UNUSED = 0x1000

    def __init__(self, filename):
        self.data = open(filename, "rb").read()
        self.marks = [0] * len(self.data)

    def mark(self, addr, mark):
        self.marks[addr] |= mark

    def hasMark(self, addr, mark):
        return bool(self.marks[addr] & mark)

    def dumpStats(self):
        stats = {}
        for mark in self.marks:
            stats[mark] = stats.get(mark, 0) + 1
        total = sum(stats.values())
        for k, v in sorted(stats.items()):
            print("%04x: %-3d (%f%%)" % (k, v, v * 100 / total))
