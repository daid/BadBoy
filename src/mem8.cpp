#include "mem8.h"
#include "card.h"


void Mem8::set(uint8_t value)
{
    origin = nullptr;
    setImpl(value);
}

void Mem8::set(Mem8& other)
{
    if (other.origin)
        origin = other.origin;
    else
        origin = &other;
    if ((id & ID_MASK) != ID_MASK)
        origin->used_as = (origin->used_as & MARK_MASK) | id;
    setImpl(other.get());
}

void Mem8::mark(uint64_t mark)
{
    used_as |= mark;
    used_as &=~MARK_BANK_MASK;
    used_as |= uint64_t(card.rom_upper_bank) << MARK_BANK_SHIFT;
}

void Mem8::markOrigin(uint64_t mark)
{
    if (origin)
        origin->mark(mark);
}

void Mem8::dumpInstrumentation(FILE* f) const
{
    if (id == std::numeric_limits<uint64_t>::max())
        return;
    if (!used_as)
        return;
    fwrite(&id, sizeof(id), 1, f);
    fwrite(&used_as, sizeof(used_as), 1, f);
}
