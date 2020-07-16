

def jumpTable(dis, addr, params):
    if len(params) > 0:
        assert len(params) == 1
        for n in range(int(params[0])):
            target = dis.info.markAsCodePointer(dis.rom, addr)
            if target is not None:
                dis.instr_addr_todo.append(target)
            addr += 2
    else:
        first = True
        while addr not in dis.info.rom_symbols or first:
            first = False
            target = dis.info.markAsCodePointer(dis.rom, addr)
            if target is not None:
                dis.instr_addr_todo.append(target)
            addr += 2

def gfx(dis, addr, params):
    assert len(params) == 0
    first = True
    while addr not in dis.info.rom_symbols or first:
        first = False
        dis.info.rom[addr] = dis.info.MARK_DATA | dis.info.ID_VRAM
        addr += 1

def dataRecords(dis, addr, params):
    assert len(params) == 2
    count = int(params[0])
    size = int(params[1])
    def formatDataRecord(output, addr):
        dis.formatLine(output, addr, size, "db   " + ", ".join(map(lambda n: "$%02x" % (n), dis.rom.data[addr:addr + size])), is_data=True)
        return addr + size
    for n in range(count):
        dis.formatter[addr] = formatDataRecord
        addr += size

ALL = {
    "jumptable": jumpTable,
    "gfx": gfx,
    "data_records": dataRecords
}
