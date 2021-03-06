#pragma once

#include <stdint.h>
#include <stdio.h>
#include <vector>
#include <limits>

#define ID_MASK  (0xFFLL << 32)
#define ID_ROM   (0x00LL << 32)
#define ID_VRAM  (0x01LL << 32)
#define ID_SRAM  (0x02LL << 32)
#define ID_WRAM  (0x03LL << 32)
#define ID_OAM   (0x04LL << 32)
#define ID_IO    (0x05LL << 32)
#define ID_HRAM  (0x06LL << 32)
#define MARK_MASK       (0xFFLL << 40)
#define MARK_INSTR      (0x01LL << 40)
#define MARK_DATA       (0x02LL << 40)
#define MARK_PTR_LOW    (0x04LL << 40)
#define MARK_PTR_HIGH   (0x08LL << 40)
#define MARK_WORD_LOW   (0x10LL << 40)
#define MARK_WORD_HIGH  (0x20LL << 40)
#define MARK_BANK_SHIFT (48)
#define MARK_BANK_MASK  (0xFFFLL << MARK_BANK_SHIFT)

class Mem8
{
public:
    uint64_t id = std::numeric_limits<uint64_t>::max();
    uint64_t used_as = 0;
    Mem8* origin = nullptr;

    void set(Mem8& other);
    void set(uint8_t value);
    void mark(uint64_t mark);
    void markOrigin(uint64_t mark);
    void dumpInstrumentation(FILE* f) const;
    virtual uint8_t get() const = 0;
    virtual void setImpl(uint8_t) = 0;
};

template<typename T> class Mem8Block : public std::vector<T>
{
public:
    void dumpInstrumentation(FILE* f)
    {
        for(const auto& m : *this)
            m.dumpInstrumentation(f);
    }
};
