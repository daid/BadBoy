
class ROM:
    def __init__(self, filename):
        self.data = open(filename, "rb").read()

    def bankCount(self):
        return len(self.data) >> 14
