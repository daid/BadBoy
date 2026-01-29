from annotation.annotation import annotation
from block.base import Block
from block.code import CodeBlock
from romInfo import RomInfo

@annotation
def sdccFarcall(memory, addr):
    """
        The sdcc compiler has a specific construct for calling functions in different banks.
        This annotation automatically handles those calls after this function is marked.
        [TODO: Is this sdcc version specific?]
    """
    SdccFarcallCodeBlock(memory, addr)

@annotation
def sdccRLEInit(memory, addr):
    """
        When disassembling sdcc code, there generally is an RLE initialization block.
        This annotation decode this.
    """
    SdccRLEInitCodeBlock(memory, addr)


class SdccFarcallCodeBlock(CodeBlock):
    def onCall(self, from_memory, from_address, next_addr):
        SdccFarrcallInfoBlock(from_memory, next_addr)
        CodeBlock(from_memory, next_addr + 4)

class SdccFarrcallInfoBlock(Block):
    def __init__(self, memory, address):
        super().__init__(memory, address, size=4)
        
        self.__target_address = memory.word(address)
        self.__bank = memory.byte(address + 2)
        unknown = memory.byte(address + 3)
        
        print("SDCC farcall to: %02x:%04x" % (self.__bank, self.__target_address))

        try:
            target_memory = RomInfo.memoryAt(self.__target_address, RomInfo.romBank(self.__bank))
        except IndexError:
            return
        target_block = target_memory[self.__target_address]
        if target_block is None:
            target_block = CodeBlock(target_memory, self.__target_address)
        target_block.addAutoLabel(self.__target_address, address, "call")

    def export(self, file):
        try:
            target_memory = RomInfo.memoryAt(self.__target_address, RomInfo.romBank(self.__bank))
        except IndexError:
            file.dataLine(4)
            return
        label = target_memory.getLabel(self.__target_address)
        if not label:
            file.dataLine(4)
            return
        file.asmLine(4, "dw", str(label), "BANK(%s)" % (label), is_data=True)


class SdccRLEInitCodeBlock(CodeBlock):
    def onCall(self, from_memory, from_address, next_addr):
        data = SdccRLEInfoBlock(from_memory, next_addr)
        CodeBlock(from_memory, next_addr + len(data))

class SdccRLEInfoBlock(Block):
    def __init__(self, memory, address):
        super().__init__(memory, address)
        while True:
            count = memory.byte(address + len(self))
            if count & 0x80:
                count = 1
            self.resize(len(self) + 1 + count)
            if count == 0:
                break

    def export(self, file):
        while True:
            count = self.memory.byte(file.addr)
            if count & 0x80:
                count = 1
            file.dataLine(1 + count)
            if count == 0:
                break
