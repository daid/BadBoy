from autoLabel import AutoLabel


class Memory:
    def __init__(self, type, size, *, base_address=0):
        self.__blocks = [None] * size
        self.__labels = {}
        self.__comments = {}
        self.__inline_comment = {}
        self.__marks = {}
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
        assert addr >= self.base_address and addr < self.base_address + len(self.__blocks)
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

    def mark(self, addr, mark):
        if addr not in self.__marks:
            self.__marks[addr] = set()
        self.__marks[addr].add(mark)

    def hasMark(self, addr, mark):
        if addr not in self.__marks:
            return False
        return mark in self.__marks[addr]
