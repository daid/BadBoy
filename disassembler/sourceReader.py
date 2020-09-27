import os
import re

from romInfo import RomInfo


class SourceReader:
    def __init__(self, base_path):
        self.__base_path = base_path
        self.__memory = None
        self.__comments = []
        self.__inline_comment = None
        self.__label = None

    def readFile(self, filename):
        print(filename)
        f = open(os.path.join(self.__base_path, filename), "rt")
        for line in f:
            if line.startswith("SECTION"):
                self.__setMemoryTypeFromSection(line)
            if ";" in line:
                self.__gotComment(line[line.find(";")+1:].rstrip())
            if ";;" in line:
                self.__gotAddressInfo(line[line.find(";;")+2:].strip())
            if ";" in line:
                line = line[:line.find(";")]
            if line.rstrip().endswith(":"):
                self.__gotLabel(line.rstrip()[:-1])

    def __setMemoryTypeFromSection(self, line):
        section_type = line.strip().split(",")[1].strip().upper()
        if "[" in section_type:
            section_type = section_type[:section_type.find("[")]
        
        if section_type == "ROM0":
            self.__memory = RomInfo.romBank(0)
        elif section_type == "ROMX":
            bank_nr = int(re.search(r"BANK\[\$([0-9a-f]+)\]", line.strip().split(",")[2])[1], 16)
            self.__memory = RomInfo.romBank(bank_nr)
        elif section_type == "WRAM0":
            self.__memory = RomInfo.getWRam()
        elif section_type == "HRAM":
            self.__memory = RomInfo.getHRam()
        else:
            raise RuntimeError("Unknown section type: %s" % (section_type))        
    
    def __gotComment(self, comment):
        if comment.startswith(";"):
            return
        if ";;" in comment:
            comment = comment[:comment.find(";;")].rstrip()
            self.__inline_comment = comment
        else:
            self.__comments.append(comment)

    def __gotLabel(self, label):
        if label.startswith("call_") or label.startswith("jp_") or label.startswith("jr_") or label.startswith("rst_") or label.startswith("data_"):
            return
        if label.startswith(".call_") or label.startswith(".jp_") or label.startswith(".jr_") or label.startswith(".rst_") or label.startswith(".data_"):
            return
        if re.match(r"^[hw][0-9A-F]{4}$", label):
            return
        self.__label = label
    
    def __gotAddressInfo(self, info):
        m = re.match(r"[0-9a-fA-F]{2}:([0-9a-fA-F]{4})", info)
        if not m:
            m = re.match(r"([0-9a-fA-F]{4})", info)
            if not m:
                return
        addr = int(m[1], 16)

        for comment in self.__comments:
            self.__memory.addComment(addr, comment)
        if self.__inline_comment is not None:
            self.__memory.addInlineComment(addr, self.__inline_comment)
        if self.__label is not None:
            self.__memory.addLabel(addr, self.__label)
        self.__comments = []
        self.__inline_comment = None
        self.__label = None
