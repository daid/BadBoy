from autoLabel import AutoLabel


class Memory:
    def __init__(self, type, size, *, base_address=0):
        self.__blocks = [None] * size
        self.__labels = {}
        self.__comments = {}
        self.__inline_comment = {}
        self.__marks = {}
        self.__include_start = {}
        self.__include_end = {}
        self.__section_starts = {}
        self.base_address = base_address
        self.type = type

    def __len__(self):
        return len(self.__blocks)

    def __getitem__(self, index):
        return self.__blocks[index - self.base_address]

    def __setitem__(self, index, value):
        if value is None:
            assert self.__blocks[index - self.base_address] != None
            self.__blocks[index - self.base_address] = value
        else:
            # assert isinstance(value, Block)
            assert self.__blocks[index - self.base_address] == None, "$%04x %s %s" % (index, self.__blocks[index - self.base_address], value)
            self.__blocks[index - self.base_address] = value

    def addLabel(self, addr, label):
        assert addr >= self.base_address and addr < self.base_address + len(self.__blocks), "%04x: %s" % (addr, label)
        self.__labels[addr] = label
    
    def addAutoLabel(self, addr, source, type):
        assert addr >= self.base_address and addr < self.base_address + len(self.__blocks)

        label = self.__labels.get(addr, None)
        if label == None:
            label = AutoLabel(self, addr)
            self.__labels[addr] = label
        if not isinstance(label, AutoLabel):
            return
        label.addSource(source, type)

    def ensureNoLabel(self, addr):
        self.__labels[addr] = False

    def getLabel(self, addr):
        return self.__labels.get(addr, None)
    
    def getLabelBefore(self, addr):
        while addr >= 0 and (addr not in self.__labels or self.__labels[addr] == False):
            addr -= 1
        return self.__labels.get(addr, None)

    def getAllLabels(self):
        return self.__labels.items()

    def addComment(self, addr, comment):
        if addr not in self.__comments:
            self.__comments[addr] = []
        self.__comments[addr].append(comment)

    def getComments(self, addr):
        return self.__comments.get(addr, None)

    def getAllComments(self):
        return self.__comments.items()

    def addInlineComment(self, addr, comment):
        self.__inline_comment[addr] = comment

    def getInlineComment(self, addr):
        return self.__inline_comment.get(addr, None)

    def getAllInlineComments(self):
        return self.__inline_comment.items()

    def startInclude(self, addr, filename):
        if addr not in self.__include_start:
            self.__include_start[addr] = []
        self.__include_start[addr].append(filename)

    def endInclude(self, addr, amount):
        assert addr not in self.__include_end
        self.__include_end[addr] = amount

    def getIncludeStart(self, addr):
        return self.__include_start.get(addr)

    def getIncludeEnd(self, addr):
        return self.__include_end.get(addr, 0)

    def addSectionStart(self, addr, name):
        self.__section_starts[addr] = name

    def getSectionStart(self, addr):
        return self.__section_starts.get(addr, None)

    def mark(self, addr, mark):
        if addr not in self.__marks:
            self.__marks[addr] = set()
        self.__marks[addr].add(mark)

    def hasMark(self, addr, mark):
        if addr not in self.__marks:
            return False
        return mark in self.__marks[addr]
