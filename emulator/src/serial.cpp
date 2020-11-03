#include "serial.h"
#include "cpu.h"
#include <unistd.h>

Serial serial;


uint8_t Serial::SBReg::get() const
{
    return serial.data;
}

void Serial::SBReg::setImpl(uint8_t value)
{
    serial.data = value;
}

uint8_t Serial::SCReg::get() const
{
    uint8_t result = 0;
    if (serial.transfer_bits_left)
        result |= 0x81;
    if (serial.bit_transfer_cycles == 16)
        result |= 0x02;
    return result;
}

void Serial::SCReg::setImpl(uint8_t value)
{
    if ((value & 0x81) == 0x81)
    {
        serial.transfer_bits_left = 8;
        serial.start_cycle = cpu.cycles;
        serial.bit_transfer_cycles = 512;
        if (cpu.gbc && (value & 0x02))
            serial.bit_transfer_cycles = 16;

        //Write the serial data to stderr, allows for various logging/testing to be done.
        write(2, &value, 1);
    }
}

void Serial::update()
{
    if (transfer_bits_left > 0)
    {
        while(int32_t(cpu.cycles - start_cycle) < 0)
        {
            start_cycle += bit_transfer_cycles;

            data = (data << 1) | 0x01;
            transfer_bits_left -= 1;
            if (transfer_bits_left == 0)
                cpu.setInterrupt(0x08);
        }
    }
}
