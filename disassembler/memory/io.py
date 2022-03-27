from .base import Memory
from block.io import IOReg


class IOMemory(Memory):
    def __init__(self):
        super().__init__("io", 0x0080, base_address=0xFF00)

        IOReg(self, 0xFF00, "rP1")
        IOReg(self, 0xFF01, "rSB")
        IOReg(self, 0xFF02, "rSC")
        IOReg(self, 0xFF04, "rDIV")
        IOReg(self, 0xFF05, "rTIMA")
        IOReg(self, 0xFF06, "rTMA")
        IOReg(self, 0xFF07, "rTAC")
        IOReg(self, 0xFF0F, "rIF")
        IOReg(self, 0xFF10, "rNR10")
        IOReg(self, 0xFF11, "rNR11")
        IOReg(self, 0xFF12, "rNR12")
        IOReg(self, 0xFF13, "rNR13")
        IOReg(self, 0xFF14, "rNR14")
        IOReg(self, 0xFF16, "rNR21")
        IOReg(self, 0xFF17, "rNR22")
        IOReg(self, 0xFF18, "rNR23")
        IOReg(self, 0xFF19, "rNR24")
        IOReg(self, 0xFF1A, "rNR30")
        IOReg(self, 0xFF1B, "rNR31")
        IOReg(self, 0xFF1C, "rNR32")
        IOReg(self, 0xFF1D, "rNR33")
        IOReg(self, 0xFF1E, "rNR34")
        IOReg(self, 0xFF20, "rNR41")
        IOReg(self, 0xFF21, "rNR42")
        IOReg(self, 0xFF22, "rNR43")
        IOReg(self, 0xFF23, "rNR44")
        IOReg(self, 0xFF24, "rNR50")
        IOReg(self, 0xFF25, "rNR51")
        IOReg(self, 0xFF26, "rNR52")
        IOReg(self, 0xFF40, "rLCDC")
        IOReg(self, 0xFF41, "rSTAT")
        IOReg(self, 0xFF42, "rSCY")
        IOReg(self, 0xFF43, "rSCX")
        IOReg(self, 0xFF44, "rLY")
        IOReg(self, 0xFF45, "rLYC")
        IOReg(self, 0xFF46, "rDMA")
        IOReg(self, 0xFF47, "rBGP")
        IOReg(self, 0xFF48, "rOBP0")
        IOReg(self, 0xFF49, "rOBP1")
        IOReg(self, 0xFF4A, "rWY")
        IOReg(self, 0xFF4B, "rWX")
        IOReg(self, 0xFF4D, "rKEY1")
        IOReg(self, 0xFF4F, "rVBK")
        IOReg(self, 0xFF51, "rHDMA1")
        IOReg(self, 0xFF52, "rHDMA2")
        IOReg(self, 0xFF53, "rHDMA3")
        IOReg(self, 0xFF54, "rHDMA4")
        IOReg(self, 0xFF55, "rHDMA5")
        IOReg(self, 0xFF56, "rRP")
        IOReg(self, 0xFF68, "rBCPS")
        IOReg(self, 0xFF69, "rBCPD")
        IOReg(self, 0xFF6A, "rOCPS")
        IOReg(self, 0xFF6B, "rOCPD")
        IOReg(self, 0xFF70, "rSVBK")

    def addAutoLabel(self, addr, source, type):
        pass


class IERegMemory(Memory):
    def __init__(self):
        super().__init__("io", 0x0001, base_address=0xFFFF)
        IOReg(self, 0xFFFF, "rIE")
