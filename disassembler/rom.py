import hashlib


class ROM:
    def __init__(self, filename):
        self.__data = open(filename, "rb").read()
    
    def __getitem__(self, index):
        return self.__data[index]
    
    def __len__(self):
        return len(self.__data)

    def bankCount(self):
        return (len(self) + 0x3fff) // 0x4000

    def md5sum(self):
        return hashlib.md5(self.__data).hexdigest()
