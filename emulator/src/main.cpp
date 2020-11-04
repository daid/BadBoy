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
#include "serial.h"
#include "mm.h"
#include "ezflash.h"


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
                //fprintf(stderr, "%08d %02x:%04x %2x %02x SP:%04x A:%02x BC:%04x DE:%04x HL:%04x F:%c%c%c%c\n", cpu.cycles, card.rom_upper_bank, cpu.pc, mm::get(cpu.pc).get(), video.LY.get(), cpu.getSP(), cpu.A.get(), cpu.getBC(), cpu.getDE(), cpu.getHL(), cpu.F.Z ? 'Z' : ' ', cpu.F.N ? 'N' : ' ', cpu.F.H ? 'H' : ' ', cpu.F.C ? 'C' : ' ');
                done[cpu.pc] = true;
            }
            {
                //static FILE* log;
                //if (!log) log = fopen("log.txt", "wt");
                //fprintf(log, "%08d %02x:%04x %2x %02x SP:%04x A:%02x BC:%04x DE:%04x HL:%04x F:%c%c%c%c\n", cpu.cycles, card.rom_upper_bank, cpu.pc, mm::get(cpu.pc).get(), video.LY.get(), cpu.getSP(), cpu.A.get(), cpu.getBC(), cpu.getDE(), cpu.getHL(), cpu.F.Z ? 'Z' : ' ', cpu.F.N ? 'N' : ' ', cpu.F.H ? 'H' : ' ', cpu.F.C ? 'C' : ' ');
            }
            if (res.type == Opcode::ERROR)
            {
                fprintf(stderr, "illegal opcode\n");
                break;
            }
            cpu.execute(res);
        }
        if (video.update())
            input.update();
        timer.update();
        serial.update();
    }
}

void usage(const char* app)
{
    fprintf(stderr, "Usage: %s rom.gb[c] [options]\n", app);
    fprintf(stderr, "Options:\n");
    fprintf(stderr, "  -o <instrumentation_file>            Write an instrumentation file from this run.\n");
    fprintf(stderr, "  -r <replay_file>                     Use the given replay file default for recording.\n");
    fprintf(stderr, "  -p                                   Play back the replay file.\n");
    fprintf(stderr, "  -s <screenshot>                      Save a screenshot on exit.\n");
}

int main(int argc, char** argv)
{
    std::string rom_file;
    std::string output_instrumentation_file;
    std::string replay_file;
    bool replay_playback = false;
    const char* ezflash = nullptr;
    const char* screenshot = nullptr;

    int c;
    while((c = getopt(argc, argv, "-o:r:pe:s:")) != -1)
    {
        switch(c)
        {
        case 1: rom_file = optarg; break;
        case 'o': output_instrumentation_file = optarg; break;
        case 'r': replay_file = optarg; break;
        case 'p': replay_playback = true; break;
        case 's': screenshot = optarg; break;
        case 'e': ezflash = optarg; break;
        case '?': usage(argv[0]); return 1;
        }
    }
    if (rom_file.empty())
    {
        fprintf(stderr, "No rom file given\n");
        usage(argv[0]);
        return 1;
    }

    card.load(rom_file.c_str());
    if (!replay_file.empty())
        input.setReplayFile(replay_file.c_str(), replay_playback);
    cpu.reset();

    if (ezflash)
        card.mbc = std::make_unique<EZFlashMBC>(ezflash);

    coreLoop();
    fprintf(stderr, "Done: %02x:%04x:%02x:%d\n", card.mbc->getRomBankNr(), cpu.pc, mm::get(cpu.pc).get(), cpu.halt);
    fprintf(stderr, "SP:%04x A:%02x BC:%04x DE:%04x HL:%04x F:%c%c%c%c\n", cpu.getSP(), cpu.A.get(), cpu.getBC(), cpu.getDE(), cpu.getHL(), cpu.F.Z ? 'Z' : ' ', cpu.F.N ? 'N' : ' ', cpu.F.H ? 'H' : ' ', cpu.F.C ? 'C' : ' ');

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
    if (screenshot)
        video.screenshot(screenshot);
    return 0;
}
