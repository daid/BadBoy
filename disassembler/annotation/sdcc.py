from annotation.annotation import annotation
from block.base import Block
from block.code import CodeBlock
from romInfo import RomInfo

@annotation
def sdccFarcall(memory, addr):
    SdccFarcallCodeBlock(memory, addr)


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
        
        file.dataLine(4)
