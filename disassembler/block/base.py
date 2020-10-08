from memory.base import Memory


class Block:
    def __init__(self, memory, base_address, *, size=0):
        assert isinstance(memory, Memory)

        self.__memory = memory
        self.__size = 0
        self.__base_address = base_address
        
        self.resize(size)

    @property
    def memory(self):
        return self.__memory

    @property
    def base_address(self):
        return self.__base_address

    def __len__(self):
        return self.__size

    def resize(self, new_size, *, allow_fail=False):
        assert new_size >= self.__size
        if allow_fail:
            for n in range(self.__size, new_size):
                if self.__memory[n + self.__base_address]:
                    return False
        for n in range(self.__size, new_size):
            self.__memory[n + self.__base_address] = self
        self.__size = new_size
        return True

    def addLabel(self, addr, label):
        assert addr >= self.__base_address and addr < self.__base_address + self.__size
        self.__memory.addLabel(addr, label)
    
    def addAutoLabel(self, addr, source, type):
        assert addr >= self.__base_address and addr < self.__base_address + self.__size
        self.__memory.addAutoLabel(addr, source, type)

    def getLabel(self, addr):
        return self.__memory.getLabel(addr)

    def export(self, file):
        raise NotImplementedError("Export not implemented for block type: %s" % (self.__class__.__name__))
