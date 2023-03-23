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
    if signed:
        memory.setValueFormatFunction(addr, _formatNumberSigned)
    elif hex:
        memory.setValueFormatFunction(addr, _formatNumberHex)
    else:
        memory.setValueFormatFunction(addr, _formatNumber)

@annotation(name="=ptr", priority=10)
def value(memory, addr, target=None, *, bank=None):
    memory.mark(addr, "PTR")
    if target is not None:
        memory.mark(addr, "PTR_TARGET", target)
    if bank is not None:
        memory.mark(addr, "PTR_BANK", int(bank, 16))

@annotation(name="=bank", priority=10)
def bank(memory, addr, target):
    memory.setValueFormatFunction(addr, lambda n: f"BANK({target})")

@annotation(name="=high", priority=10)
def bank(memory, addr, target):
    memory.setValueFormatFunction(addr, lambda n: f"HIGH({target})")

@annotation(name="=low", priority=10)
def bank(memory, addr, target):
    memory.setValueFormatFunction(addr, lambda n: f"LOW({target})")

