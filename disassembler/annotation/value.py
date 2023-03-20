import re
from annotation.annotation import annotation


def _formatNumber(value):
    return f"{value}"

def _formatNumberSigned(value):
    if value >= 0x8000:
        return f"{value-0x10000}"
    return f"{value}"


@annotation(name="=value", priority=1000)
def value(memory, addr, *, signed=False):
    if signed:
        memory.setValueFormatFunction(addr, _formatNumberSigned)
    else:
        memory.setValueFormatFunction(addr, _formatNumber)

@annotation(name="=ptr", priority=1000)
def value(memory, addr, target=None):
    memory.mark(addr, "PTR")
    if target is not None:
        memory.mark(addr, "PTR_TARGET", target)

@annotation(name="=bank", priority=1000)
def bank(memory, addr, target):
    memory.setValueFormatFunction(addr, lambda n: f"BANK({target})")

@annotation(name="=high", priority=1000)
def bank(memory, addr, target):
    memory.setValueFormatFunction(addr, lambda n: f"HIGH({target})")

@annotation(name="=low", priority=1000)
def bank(memory, addr, target):
    memory.setValueFormatFunction(addr, lambda n: f"LOW({target})")

