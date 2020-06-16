#include "mem8.h"

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
}

void Mem8::markOrigin(uint64_t mark)
{
    if (origin)
        origin->used_as |= mark;
}
