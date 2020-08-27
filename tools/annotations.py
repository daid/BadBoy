

def jumpTable(dis, addr, params):
    if len(params) > 0:
        assert len(params) < 3
        label_format = params[1] if len(params) > 1 else None
        for n in range(int(params[0])):
            if label_format:
                target = dis.info.markAsCodePointer(dis.rom, addr, name=label_format % (n))
            else:
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

def pointerTable(dis, addr, params):
    assert 0 < len(params) < 2
    label_format = params[1] if len(params) > 1 else None
    for n in range(int(params[0])):
        if label_format:
            target = dis.info.markAsPointer(dis.rom, addr, name=label_format % (n))
        else:
            target = dis.info.markAsPointer(dis.rom, addr)
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

def bank(dis, addr, params):
    assert len(params) == 1
    bank = int(params[0])
    dis.info.setActiveBank(addr, bank)
    dis.info.setActiveBank(addr + 1, bank)
    dis.info.setActiveBank(addr + 2, bank)

ALL = {
    "jumptable": jumpTable,
    "gfx": gfx,
    "data_records": dataRecords,
    "bank": bank,
    "pointertable": pointerTable,
}
