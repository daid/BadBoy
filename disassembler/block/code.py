from .base import Block
from instruction import *
from romInfo import RomInfo

CART_CONTROL_REGS = {
    0x0000: "$0000",
    0x2000: "$2000",
    0x2100: "$2100",
}


class CodeBlock(Block):
    def __init__(self, memory, address):
        super().__init__(memory, address)
        
        while True:
            if address >= 0x8000 or memory[address]:
                break

            try:
                instr = Instruction(self.memory, address)
            except InstructionDecodeError:
                print("Encountered invalid instruction [%02x] in code at: %02x:%04x" % (memory.byte(address), memory.bankNumber, address))
                break
            if not self.resize(len(self) + instr.size, allow_fail=True):
                print("Odd instruction overlap at: %02x:%04x" % (memory.bankNumber, address))
                break

            for n in range(1, instr.size):
                memory.ensureNoLabel(address + n)
            address += instr.size
            
            target = instr.jumpTarget()
            if target != None and target < 0x8000:
                if memory.bankNumber > 0:
                    active_bank = memory
                else:
                    active_bank = memory.activeRomBankAt(address - instr.size)
                    if active_bank is not None:
                        active_bank = RomInfo.romBank(active_bank)
                other_memory = RomInfo.memoryAt(target, active_bank)
                if other_memory:
                    other_block = other_memory[target]
                    if other_block == None:
                        CodeBlock(other_memory, target)
                        other_block = other_memory[target]
                    elif isinstance(other_block, CodeBlock):
                        if instr.type in (CALL, RST):
                            other_block.onCall(self.memory, address - instr.size, address)
                        else:
                            other_block.onJump(self.memory, address - instr.size, address)
                    other_block.addAutoLabel(target, address, instr.type)
            elif isinstance(instr.p0, Ref) and isinstance(instr.p0.target, int) and instr.p0.target >= 0x8000:
                mem = RomInfo.memoryAt(instr.p0.target, memory)
                if mem:
                    mem.addAutoLabel(instr.p0.target, address, "data")
            elif isinstance(instr.p1, Ref) and isinstance(instr.p1.target, int):
                mem = RomInfo.memoryAt(instr.p1.target, memory)
                if mem:
                    mem.addAutoLabel(instr.p1.target, address, "data")
            elif instr.p0 in (BC, DE, HL) and isinstance(instr.p1, int):
                if 0x4000 <= instr.p1 < 0x8000 and memory.bankNumber > 0: # Banked ROM
                    RomInfo.memoryAt(instr.p1, memory).addAutoLabel(instr.p1, address, "data")
                elif 0xC000 <= instr.p1 < 0xE000: # WRAM
                    RomInfo.memoryAt(instr.p1).addAutoLabel(instr.p1, address, "data")
                elif 0xFF80 <= instr.p1 < 0xFFFF: # HRAM
                    RomInfo.memoryAt(instr.p1).addAutoLabel(instr.p1, address, "data")
            if not instr.hasNext():
                break

    def export(self, file):
        while file.addr < self.base_address + len(self):
            self.outputInstruction(file, Instruction(self.memory, file.addr))

    def outputInstruction(self, file, instr):
        p0 = instr.p0
        p1 = instr.p1
        if instr.type in (JP, JR, CALL, RST) and p0 != HL:
            p0 = self.formatAsAddressOrLabel(p0, file.addr)

        # Prevent the assembler from optimizing "LD [FFxx], A" and "LD A, [FFxx]" instructions.
        if instr.type == LD and isinstance(p0, Ref) and isinstance(p0.target, int) and p0.target >= 0xFF00 and instr.p1 == A:
            instr.type = "ld_long_store"
            p0 = "%s" % (self.formatAsAddressOrLabel(p0.target, file.addr))
        elif instr.type == LD and isinstance(p1, Ref) and isinstance(p1.target, int) and p1.target >= 0xFF00 and instr.p0 == A:
            instr.type = "ld_long_load"
            p1 = "%s" % (self.formatAsAddressOrLabel(p1.target, file.addr))

        if isinstance(p0, Ref) and isinstance(p0.target, int):
            if p0.target in CART_CONTROL_REGS:
                p0 = "[%s]" % CART_CONTROL_REGS[p0.target]
            else:
                p0 = "[%s]" % (self.formatAsAddressOrLabel(p0.target, file.addr))
        if isinstance(p1, Ref) and isinstance(p1.target, int):
            p1 = "[%s]" % (self.formatAsAddressOrLabel(p1.target, file.addr))

        if isinstance(p0, int) and instr.type not in (SET, RES, BIT):
            p0 = self.formatAsNumberOrLabel(p0, file.addr)
        if isinstance(p1, int) and (instr.type != ADD or instr.p0 != SP):
            p1 = self.formatAsNumberOrLabel(p1, file.addr)

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

    def formatAsAddressOrLabel(self, target, source_addr):
        label = RomInfo.getLabelAt(target, RomInfo.romBank(self.memory.activeRomBankAt(source_addr)))
        if label:
            label = str(label)
            dot = label.find(".")
            if dot > 0:
                prefix = label[:dot]
                if str(self.memory.getLabelBefore(source_addr)) == prefix:
                    return label[dot:]
            return label
        return "$%04x" % (target)

    def formatAsNumberOrLabel(self, target, source_addr):
        if target < 0x1000 or target == 0xFF00:
            return "$%02x" % (target)
        return self.formatAsAddressOrLabel(target, source_addr)

    def onCall(self, from_memory, from_addr, next_addr):
        pass

    def onJump(self, from_memory, from_addr, next_addr):
        pass
