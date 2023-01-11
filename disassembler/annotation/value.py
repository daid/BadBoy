import re
from annotation.annotation import annotation


@annotation(name="=value", priority=1000)
def value(memory, addr, *, signed=False):
    memory.mark(addr, "VALUE")
    if signed:
        memory.mark(addr, "SIGNED")

@annotation(name="=ptr", priority=1000)
def value(memory, addr, target=None):
    memory.mark(addr, "PTR")
    if target is not None:
        memory.mark(addr, "PTR_TARGET", target)

@annotation(name="=bank", priority=1000)
def bank(memory, addr, target):
    memory.mark(addr, "BANK_TARGET", target)
