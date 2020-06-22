
class ROM:
    def __init__(self, filename):
        self.data = open(filename, "rb").read()
