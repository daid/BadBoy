import re
from annotation.annotation import annotation


def _formatNumber(value):
    return f"{value}"

def _formatNumberSigned(value):
    if value >= 0x8000:
        return f"{value-0x10000}"
    return f"{value}"

def _formatNumberHex(value):
    return f"${value:04x}"


@annotation(name="=value", priority=10)
def value(memory, addr, *, signed=False, hex=False):
    """
        Mark the data of an instruction as a value, guarantees it is not seen as a pointer.

        ld  hl, $4000 ;@=value hex=True
        ld  hl, 16384 ;@=value
        ld  hl, -16384 ;@=value signed=True
    """
    if signed:
        memory.setValueFormatFunction(addr, _formatNumberSigned)
    elif hex:
        memory.setValueFormatFunction(addr, _formatNumberHex)
    else:
        memory.setValueFormatFunction(addr, _formatNumber)

@annotation(name="=ptr", priority=10)
def value(memory, addr, target=None, *, bank=None):
    """
        Mark the data of an instruction as a pointer, guarantees it is seen as a pointer, instead of depending on heuristics
        Optionally specificy exactly which label it should point at or which bank the pointer is pointing at.

        ld  hl, data_00_1000 ;@=ptr
    """
    memory.mark(addr, "PTR")
    if target is not None:
        memory.mark(addr, "PTR_TARGET", target)
    if bank is not None:
        memory.mark(addr, "PTR_BANK", int(bank, 16))

@annotation(name="=bank", priority=10)
def bank(memory, addr, target):
    """
        Specify that this instruction is actually a bank of a label.

        ld a, BANK(data_02_4000) ;@=bank data_02_4000
    """
    memory.setValueFormatFunction(addr, lambda n: f"BANK({target})")

@annotation(name="=high", priority=10)
def bank(memory, addr, target):
    """
        Specify that this instruction is actually a high byte of a label.

        ld a, HIGH(data_02_4000) ;@=high data_02_4000
    """
    memory.setValueFormatFunction(addr, lambda n: f"HIGH({target})")

@annotation(name="=low", priority=10)
def bank(memory, addr, target):
    """
        Specify that this instruction is actually a low byte of a label.

        ld a, LOW(data_02_4000) ;@=low data_02_4000
    """
    memory.setValueFormatFunction(addr, lambda n: f"LOW({target})")

