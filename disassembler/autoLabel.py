

class AutoLabel:
    def __init__(self, memory, address):
        self.memory = memory
        self.address = address
        self.source_types = set()
        self.source_addresses = set()
        self.local = None
 
    def addSource(self, address, type):
        self.source_types.add(type)
        if address is not None:
            self.source_addresses.add(address)
        else:
            self.local = False
        
        if type == "call":
            self.local = False

    def __str__(self):
        prefix = "data"
        if "call" in self.source_types:
            prefix = "call"
        elif "rst" in self.source_types:
            prefix = "rst"
        elif "jp" in self.source_types:
            prefix = "jp"
        elif "jr" in self.source_types:
            prefix = "jr"

        if self.local:
            prefix = ".%s" % (prefix)

        return "%s_%02x_%04x" % (prefix, self.memory.bankNumber, self.address)


class AutoLabelLocalizer:
    def __init__(self, memory):
        self.__memory = memory
        self.__blocks_labels = {}
        
        for _, label in memory.getAllLabels():
            if not isinstance(label, AutoLabel):
                continue
            self.__processLabel(label)
    
    def __processLabel(self, auto_label):
        if auto_label.local == False:
            return
    
        source_min = auto_label.address
        source_max = auto_label.address
        
        for source in auto_label.source_addresses:
            source_min = min(source_min, source)
            source_max = max(source_max, source)
        
        labels = set()
        for addr in range(source_min, source_max + 1):
            label = self.__memory.getLabel(addr)
            if label is None:
                continue
            if isinstance(label, str):
                if not label.startswith("."):
                    self.__removeLocal(auto_label)
                    return
            elif isinstance(label, AutoLabel):
                if label.local == False:
                    self.__removeLocal(auto_label)
                    return
            labels.add(label)

        auto_label.local = True
        for label in labels:
            if label not in self.__blocks_labels:
                self.__blocks_labels[label] = set()
            self.__blocks_labels[label].add(auto_label)

    def __removeLocal(self, auto_label):
        auto_label.local = False
        if auto_label in self.__blocks_labels:
            labels = self.__blocks_labels[auto_label]
            del self.__blocks_labels[auto_label]
            for label in labels:
                self.__removeLocal(label)
