from annotation.annotation import annotation
from block.code import CodeBlock

@annotation
def code(memory, addr):
    print(hex(addr))
    CodeBlock(memory, addr)