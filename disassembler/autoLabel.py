

class AutoLabel:
    def __init__(self, memory, address):
        self.memory = memory
        self.address = address
        self.source_types = set()
        self.source_addresses = set()
    
    def addSource(self, address, type):
        self.source_types.add(type)
        self.source_addresses.add(address)
        diff = address - self.address

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

        # TODO: Figure out if this is a local label or not.
        return "%s_%02x_%04x" % (prefix, self.memory.bankNumber, self.address)
