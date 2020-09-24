from .base import Memory


class VRamMemory(Memory):
    def __init__(self):
        super().__init__("vram", 0x2000, base_address=0x8000)

class ERamMemory(Memory):
    def __init__(self):
        super().__init__("eram", 0x2000, base_address=0xA000)

class WRamMemory(Memory):
    def __init__(self):
        super().__init__("wram", 0x2000, base_address=0xC000)

class WRamMemoryBanked(Memory):
    def __init__(self, bank):
        super().__init__("wram%x" % (bank), 0x1000, base_address=0xC000 + bank * 0x1000)

class OAMMemory(Memory):
    def __init__(self):
        super().__init__("oam", 0x00A0, base_address=0xFE00)

class HRamMemory(Memory):
    def __init__(self):
        super().__init__("hram", 0xFF80, base_address=0x00FF)
