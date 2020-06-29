#include <SDL.h>
#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <string>

#include "card.h"
#include "opcodes.h"
#include "cpu.h"
#include "video.h"
#include "audio.h"
#include "input.h"
#include "timer.h"
#include "mm.h"

static void initCore()
{
    card.init();
    video.init();
    ram.init();
    for(uint32_t n=0xFF00; n<0xFF80; n++)
        mm::get(n).id = n | ID_IO;
    mm::get(0xFF7F).id = std::numeric_limits<uint64_t>::max();
    mm::get(0xFFFF).id = 0xFFFF | ID_IO;

    cpu.gbc = card.getRom(0x143).get() & 0x80;
    if (card.getBoot(0).get() == 0x00)
    {
        //Skip the bootrom and setup the defaults as they would be after the bootrom.
        cpu.A.set(cpu.gbc ? 0x11 : 0x01);
        cpu.F.set(0xB0);
        cpu.B.set(0x00);
        cpu.C.set(0x13);
        cpu.D.set(0x00);
        cpu.E.set(0xD8);
        cpu.H.set(0x01);
        cpu.L.set(0x4D);
        cpu.S.set(0xFF);
        cpu.P.set(0xFE);
        video.LCDC.set(0x91);
        video.BGP.set(0xFC);
        video.OBP0.set(0xFF);
        video.OBP1.set(0xFF);
        mm::get(0xFF50).set(0x01);
        cpu.pc = 0x100;
    }

    audio.init();
}

void coreLoop()
{
    while(!input.quit)
    {
        if (cpu.ime)
        {
            uint8_t flags = cpu.IF.get() & cpu.IE.get();
            if (flags & 0x01)
            {
                cpu.IF.set(cpu.IF.get() & ~0x01);
                cpu.interrupt(0x40);
            }
            else if (flags & 0x02)
            {
                cpu.IF.set(cpu.IF.get() & ~0x02);
                cpu.interrupt(0x48);
            }
            else if (flags & 0x04)
            {
                cpu.IF.set(cpu.IF.get() & ~0x04);
                cpu.interrupt(0x50);
            }
            else if (flags & 0x08)
            {
                cpu.IF.set(cpu.IF.get() & ~0x08);
                cpu.interrupt(0x58);
            }
            else if (flags & 0x10)
            {
                cpu.IF.set(cpu.IF.get() & ~0x10);
                cpu.interrupt(0x60);
            }
        }

        if (cpu.halt)
        {
            cpu.cycles += 4;
        }
        else
        {
            auto res = decode(cpu.pc);
            static bool done[0xFFFF];
            if (!done[cpu.pc])
            {
                //printf("%08d %02x:%04x %2x %02x SP:%04x A:%02x BC:%04x DE:%04x HL:%04x F:%c%c%c%c\n", cpu.cycles, card.rom_upper_bank, cpu.pc, mm::get(cpu.pc).get(), video.LY.get(), cpu.getSP(), cpu.A.get(), cpu.getBC(), cpu.getDE(), cpu.getHL(), cpu.F.Z ? 'Z' : ' ', cpu.F.N ? 'N' : ' ', cpu.F.H ? 'H' : ' ', cpu.F.C ? 'C' : ' ');
                done[cpu.pc] = true;
            }
            {
                //static FILE* log;
                //if (!log) log = fopen("log.txt", "wt");
                //fprintf(log, "%08d %02x:%04x %2x %02x SP:%04x A:%02x BC:%04x DE:%04x HL:%04x F:%c%c%c%c\n", cpu.cycles, card.rom_upper_bank, cpu.pc, mm::get(cpu.pc).get(), video.LY.get(), cpu.getSP(), cpu.A.get(), cpu.getBC(), cpu.getDE(), cpu.getHL(), cpu.F.Z ? 'Z' : ' ', cpu.F.N ? 'N' : ' ', cpu.F.H ? 'H' : ' ', cpu.F.C ? 'C' : ' ');
            }
            if (res.type == Opcode::ERROR)
                break;
            cpu.execute(res);
        }
        if (video.update())
            input.update();
        timer.update();
    }
}

int main(int argc, char** argv)
{
    std::string rom_file;
    std::string output_instrumentation_file;
    std::string replay_file;
    bool replay_playback = false;

    int c;
    while((c = getopt(argc, argv, "-o:r:p")) != -1)
    {
        switch(c)
        {
        case 1: rom_file = optarg; break;
        case 'o': output_instrumentation_file = optarg; break;
        case 'r': replay_file = optarg; break;
        case 'p': replay_playback = true; break;
        }
    }
    if (rom_file.empty())
    {
        printf("No rom file given");
        return 1;
    }

    card.load(rom_file.c_str());
    if (!replay_file.empty())
        input.setReplayFile(replay_file.c_str(), replay_playback);
    initCore();

    coreLoop();
    printf("Done: %02x:%04x:%02x:%d\n", card.rom_upper_bank, cpu.pc, mm::get(cpu.pc).get(), cpu.halt);

    if (!output_instrumentation_file.empty())
    {
        FILE* f = fopen(output_instrumentation_file.c_str(), "wb");
        if (f)
        {
            card.dumpInstrumentation(f);
            ram.dumpInstrumentation(f);
            video.dumpInstrumentation(f);
            fclose(f);
        }
    }
    return 0;
}
