from .base import Block


class IOReg(Block):
    def __init__(self, memory, base_address, label, *, size=1):
        super().__init__(memory, base_address, size=size)

        self.addLabel(base_address, label)
