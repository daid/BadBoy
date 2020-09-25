from .base import Block
from instruction import *
from romInfo import RomInfo

CART_CONTROL_REGS = {
    0x0000: "MBCSRamEnable",
    0x2000: "$2000",
    0x2100: "MBCBankSelect",
}


class CodeBlock(Block):
    def __init__(self, memory, address):
        super().__init__(memory, address)
        
        while True:
            if memory[address]:
                break

            try:
                instr = Instruction(self.memory, address)
            except InstructionDecodeError:
                print("Encountered invalid instruction in code at: %02x:%04x" % (memory.bankNumber, address))
                break
            if not self.resize(len(self) + instr.size, allow_fail=True):
                print("Odd instruction overlap at: %02x:%04x" % (memory.bankNumber, address))
                break
            address += instr.size
            
            target = instr.jumpTarget()
            if target != None and target < 0x8000:
                if memory[target] == None:
                    CodeBlock(memory, target)
                memory[target].addAutoLabel(target, address, instr.type)
            elif isinstance(instr.p0, Ref) and isinstance(instr.p0.target, int):
                mem = RomInfo.memoryAt(instr.p0.target, memory)
                if mem:
                    mem.addAutoLabel(instr.p0.target, address, "data")
            elif isinstance(instr.p1, Ref) and isinstance(instr.p1.target, int):
                mem = RomInfo.memoryAt(instr.p1.target, memory)
                if mem:
                    mem.addAutoLabel(instr.p1.target, address, "data")
            
            if not instr.hasNext():
                break

    def export(self, file):
        while file.addr < self.base_address + len(self):
            self.outputInstruction(file, Instruction(self.memory, file.addr))

    def outputInstruction(self, file, instr):
        p0 = instr.p0
        p1 = instr.p1
        if instr.type in (JP, JR, CALL, RST) and p0 != HL:
            p0 = self.formatAsAddressOrLabel(p0)

        if isinstance(p0, Ref) and isinstance(p0.target, int):
            if p0.target in CART_CONTROL_REGS:
                p0 = "[%s]" % CART_CONTROL_REGS[p0.target]
            else:
                p0 = "[%s]" % (self.formatAsAddressOrLabel(p0.target))
        if isinstance(p1, Ref) and isinstance(p1.target, int):
            p1 = "[%s]" % (self.formatAsAddressOrLabel(p1.target))

        if isinstance(p0, int):
            p0 = self.formatAsNumberOrLabel(p0)
        if isinstance(p1, int) and (instr.type != ADD or instr.p0 != SP):
            p1 = self.formatAsNumberOrLabel(p1)
        
        if instr.condition != None and instr.p0 != None:
            file.asmLine(instr.size, instr.type, instr.condition, str(p0))
        elif instr.p0 != None and instr.p1 != None:
            file.asmLine(instr.size, instr.type, str(p0), str(p1))
        elif instr.p0 != None:
            file.asmLine(instr.size, instr.type, str(p0))
        elif instr.condition != None:
            file.asmLine(instr.size, instr.type, instr.condition)
        else:
            file.asmLine(instr.size, instr.type)

    def formatAsAddressOrLabel(self, addr):
        label = RomInfo.getLabelAt(addr, self.memory)
        if label:
            return label
        return "$%04x" % (addr)

    def formatAsNumberOrLabel(self, number):
        if number < 0x1000 or number == 0xFF00:
            return "$%02x" % (number)
        return self.formatAsAddressOrLabel(number)
