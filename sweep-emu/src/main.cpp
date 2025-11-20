#include "emulator.h"
#include "platform.h"
#include <getopt.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/stat.h>
#include <string>
#include <vector>
#include <SDL.h>

extern "C" {
    //These functions are defined by binjgb, but not in the header file.
    void emulator_write_mem(Emulator* e, u16 addr, u8 data);
    u8 emulator_read_mem(Emulator* e, u16 addr);
}

class InfoBar
{
public:
    InfoBar()
    {
        backbuffer = SDL_CreateRGBSurface(0, SCREEN_WIDTH, 16, 32, 0, 0, 0, 0);
        SDL_LockSurface(backbuffer);
    }

    void setStatus(std::string line0, std::string line1, int cursor_x=-1, int cursor_y=-1, int cursor_width=1)
    {
        clear();
        if (cursor_x >= 0 && cursor_y >= 0) {
            RGBA* dst = &((uint32_t*)backbuffer->pixels)[cursor_y * 8 * SCREEN_WIDTH + cursor_x * (GLYPH_WIDTH + 1)];
            for(int y=0; y<8; y++) {
                for(int x=0; x<(GLYPH_WIDTH+1) * cursor_width; x++) {
                    dst[x] = 0x800080;
                }
                dst += SCREEN_WIDTH;
            }
        }
        int x = 0;
        for(auto c : line0) {
            drawChar(x, 1, 0xFFFFFF, c);
            x += GLYPH_WIDTH + 1;
        }
        x = 0;
        for(auto c : line1) {
            drawChar(x, 9, 0xFFFFFF, c);
            x += GLYPH_WIDTH + 1;
        }
    }

    void draw(SDL_Surface* window_surface, int scale)
    {
        SDL_UnlockSurface(backbuffer);
        SDL_Rect window_rect{0, 144*scale, 160*scale,16*scale};
        SDL_BlitScaled(backbuffer, nullptr, window_surface, &window_rect);
        SDL_LockSurface(backbuffer);
    }

private:
    void clear()
    {
        memset(backbuffer->pixels, 0, 160 * 16 * sizeof(uint32_t));
    }

    void drawChar(int x, int y, RGBA color, char c)
    {
        /* For now, don't clamp. */
        u8 uc = (u8)c;
        if (uc < 32 || uc >= 128) return;
        u16 data = s_font[uc - 32];
        bool has_descender = data & 1;
        data >>= 1;
        if (has_descender) y += 1;
        int i, j;
        RGBA* dst = &((uint32_t*)backbuffer->pixels)[y * SCREEN_WIDTH + x];
        for (j = 0; j < GLYPH_HEIGHT; ++j) {
            for (i = 0; i < GLYPH_WIDTH; ++i) {
                if (data & 1) *dst = color;
                data >>= 1;
                dst++;
            }
            dst += SCREEN_WIDTH - GLYPH_WIDTH;
        }
    }

private:
    SDL_Surface* backbuffer = nullptr;

    static constexpr int GLYPH_WIDTH = 3;
    static constexpr int GLYPH_HEIGHT = 5;
    static constexpr int GLYPHS_PER_LINE = ((SCREEN_WIDTH / (GLYPH_WIDTH + 1)) - 1);

    /* tom-thumb font: https://robey.lag.net/2010/01/23/tiny-monospace-font.html
     * license: CC0
     */
    static constexpr u16 s_font[] = {
        0x0000, 0x4124, 0x005a, 0xbefa, 0x4f3c, 0x8542, 0xd7b6, 0x0024, 0x8928,
        0x2922, 0x02aa, 0x0ba0, 0x2800, 0x0380, 0x4000, 0x2548, 0x76dc, 0x4934,
        0xe546, 0x7146, 0x93da, 0x719e, 0xf79c, 0x254e, 0xf7de, 0x73de, 0x0820,
        0x2820, 0x88a8, 0x1c70, 0x2a22, 0x414e, 0xc7d4, 0xb7d4, 0x75d6, 0xc49c,
        0x76d6, 0xe79e, 0x279e, 0xd79c, 0xb7da, 0xe92e, 0x5648, 0xb5da, 0xe492,
        0xb7fa, 0xbffa, 0x56d4, 0x25d6, 0xded4, 0xafd6, 0x711c, 0x492e, 0xd6da,
        0x4ada, 0xbfda, 0xb55a, 0x495a, 0xe54e, 0xe49e, 0x1110, 0xf24e, 0x0054,
        0xe000, 0x0022, 0xf730, 0x76b2, 0xc4e0, 0xd6e8, 0xcee0, 0x4ba8, 0x53dd,
        0xb6b2, 0x4904, 0x5641, 0xadd2, 0xe926, 0xbff0, 0xb6b0, 0x56a0, 0x2ed7,
        0x9add, 0x24e0, 0x79e0, 0xc974, 0xd6d0, 0x5ed0, 0xffd0, 0xa950, 0x535b,
        0xef70, 0xc8ac, 0x4824, 0x6a26, 0x003c, 0xfffe,
    };
};

class MainEmulator
{
public:
    MainEmulator(const char* rom_filename)
    {
        EmulatorInit init = {0};
        if (file_read(rom_filename, &init.rom)) {
            fprintf(stderr, "Failed to read ROM file\n");
            return;
        }
        init.audio_frequency = 44100;
        init.audio_frames = 2048;
        init.builtin_palette = 83;
        init.cgb_color_curve = CGB_COLOR_CURVE_SAMEBOY_EMULATE_HARDWARE;
        emu = emulator_new(&init);

        backbuffer = SDL_CreateRGBSurface(0, SCREEN_WIDTH, SCREEN_HEIGHT, 32, 0, 0, 0, 0);

        SDL_AudioSpec desired = {0};
        desired.channels = 2;
        desired.format = AUDIO_U8;
        desired.freq = 44100;
        audio_device = SDL_OpenAudioDevice(nullptr, false, &desired, nullptr, false);
        SDL_PauseAudioDevice(audio_device, 0);
    }

    void handleKey(SDL_Keycode key, bool down)
    {
        if (key == SDLK_DOWN) joypad_buttons.down = down ? TRUE : FALSE;
        if (key == SDLK_UP) joypad_buttons.up = down ? TRUE : FALSE;
        if (key == SDLK_LEFT) joypad_buttons.left = down ? TRUE : FALSE;
        if (key == SDLK_RIGHT) joypad_buttons.right = down ? TRUE : FALSE;
        if (key == SDLK_RETURN) joypad_buttons.start = down ? TRUE : FALSE;
        if (key == SDLK_RSHIFT) joypad_buttons.select = down ? TRUE : FALSE;
        if (key == SDLK_a) joypad_buttons.B = down ? TRUE : FALSE;
        if (key == SDLK_s) joypad_buttons.A = down ? TRUE : FALSE;
        if (key == SDLK_F2 && down && !save_state.empty()) {
            FileData fd { save_state.data(), save_state.size() };
            emulator_read_state(emu, &fd);
            joypad_recording.clear();
        }
        if (key == SDLK_F4 && down) {
            save_state.resize(s_emulator_state_size);
            FileData fd { save_state.data(), save_state.size() };
            emulator_write_state(emu, &fd);
            joypad_recording.clear();
        }
    }

    void advanceFrame()
    {
        joypad_recording.push_back(joypad_buttons);
        emulator_set_joypad_buttons(emu, &joypad_buttons);
        while(true) {
            auto res = emulator_run_until(emu, emulator_get_ticks(emu) + PPU_FRAME_TICKS * 2);
            if (res & EMULATOR_EVENT_AUDIO_BUFFER_FULL) {
                auto audio_buffer = emulator_get_audio_buffer(emu);
                if (SDL_GetQueuedAudioSize(audio_device) < audio_buffer->frames * 10)
                    SDL_QueueAudio(audio_device, audio_buffer->data, audio_buffer->frames * 2);
            }
            if (res & EMULATOR_EVENT_NEW_FRAME) {
                SDL_LockSurface(backbuffer);
                memcpy(backbuffer->pixels, emulator_get_frame_buffer(emu), sizeof(FrameBuffer));
                SDL_UnlockSurface(backbuffer);
                break;
            }
            if (res & EMULATOR_EVENT_UNTIL_TICKS) {
                break;
            }
            if (res & EMULATOR_EVENT_INVALID_OPCODE) {
                break;
            }
        }
    }

    void draw(SDL_Surface* window_surface, int scale)
    {
        SDL_Rect window_rect{0, 0, 160*scale,144*scale};
        SDL_BlitScaled(backbuffer, nullptr, window_surface, &window_rect);
    }

    ~MainEmulator()
    {
        emulator_delete(emu);
    }

    bool hasSaveState()
    {
        return !save_state.empty();
    }

    std::vector<uint8_t> getSaveState()
    {
        return save_state;
    }

    std::vector<JoypadButtons> getRecording()
    {
        return joypad_recording;
    }

    bool romLoaded()
    {
        return emu != nullptr;
    }

private:
    JoypadButtons joypad_buttons = {FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE};
    Emulator* emu = nullptr;
    SDL_Surface* backbuffer = nullptr;
    SDL_AudioDeviceID audio_device = 0;
    std::vector<uint8_t> save_state;
    std::vector<JoypadButtons> joypad_recording;
};

class Sweeper
{
public:
    Sweeper(MainEmulator& main_emulator, const char* rom_filename)
    : main_emulator(main_emulator)
    {
        if (file_read(rom_filename, &base_rom_file)) {
            fprintf(stderr, "Failed to read ROM file\n");
            return;
        }

        backbuffer = SDL_CreateRGBSurface(0, SCREEN_WIDTH, SCREEN_HEIGHT, 32, 0, 0, 0, 0);
    }

    void handleKey(SDL_Keycode key, bool down)
    {
        if (run_state != RunState::Inactive) return;
        if (!down) return;
        if (key == SDLK_RIGHT) cursor_pos = cursor_pos == CursorPos::Value1 ? CursorPos::Type : (CursorPos)((int)cursor_pos + 1);
        if (key == SDLK_LEFT) cursor_pos = cursor_pos == CursorPos::Type ? CursorPos::Value1 : (CursorPos)((int)cursor_pos - 1);
        if (key >= SDLK_0 && key <= SDLK_9) { setCurrent(key - SDLK_0); cursor_pos = cursor_pos == CursorPos::Value1 ? CursorPos::Type : (CursorPos)((int)cursor_pos + 1); }
        if (key >= SDLK_a && key <= SDLK_f) { setCurrent(key - SDLK_a + 10); cursor_pos = cursor_pos == CursorPos::Value1 ? CursorPos::Type : (CursorPos)((int)cursor_pos + 1); }
        if (key == SDLK_UP) setCurrent(getCurrent() + 1);
        if (key == SDLK_DOWN) setCurrent(getCurrent() - 1);
        if (key == SDLK_RETURN && isValid()) {
            run_state = RunState::ReferenceImage;
            current_address = target_addr_start;

            makedir("output");
            char filename[32];
            sprintf(filename, "output/%s-%02x.%04x-%04x", typeToString[int(target_type)], target_bank, target_addr_start, target_addr_end);
            makedir(filename);
        }
    }

    void update()
    {
        if (run_state == RunState::Inactive) return;
        auto start_tick = SDL_GetTicks();
        while(SDL_GetTicks() - start_tick < 100)
            step();
    }

    void step() {
        if (run_state == RunState::Inactive) return;
        EmulatorInit init = {0};
        init.rom.data = (uint8_t*)malloc(base_rom_file.size);
        memcpy(init.rom.data, base_rom_file.data, base_rom_file.size);
        if (run_state == RunState::Sweeping && target_type == TargetType::ROM) {
            auto ptr = &init.rom.data[target_bank * 0x4000 + (current_address & 0x3FFF)];
            *ptr = applySweep(*ptr);
        }
        init.rom.size = base_rom_file.size;
        init.audio_frequency = 44100;
        init.audio_frames = 2048;
        init.builtin_palette = 83;
        init.cgb_color_curve = CGB_COLOR_CURVE_SAMEBOY_EMULATE_HARDWARE;
        auto emu = emulator_new(&init);
        auto save_state = main_emulator.getSaveState();
        auto joypad_data = main_emulator.getRecording();
        FileData fd = {save_state.data(), save_state.size()};
        emulator_read_state(emu, &fd);
        if (run_state == RunState::Sweeping && target_type != TargetType::ROM) {
            //TODO: Handle WRAM banking.
            emulator_write_mem(emu, current_address, applySweep(emulator_read_mem(emu, current_address)));
        }
        while(!joypad_data.empty()) {
            auto res = emulator_run_until(emu, emulator_get_ticks(emu) + PPU_FRAME_TICKS * 2);
            if (res & (EMULATOR_EVENT_NEW_FRAME | EMULATOR_EVENT_UNTIL_TICKS)) {
                joypad_data.erase(joypad_data.begin());
                if (!joypad_data.empty())
                    emulator_set_joypad_buttons(emu, &joypad_data.front());
            }
            if (res & EMULATOR_EVENT_INVALID_OPCODE)
                break;
        }

        SDL_LockSurface(backbuffer);
        memcpy(backbuffer->pixels, emulator_get_frame_buffer(emu), sizeof(FrameBuffer));
        SDL_UnlockSurface(backbuffer);

        if (run_state == RunState::ReferenceImage) {
            run_state = RunState::Sweeping;
            current_address = target_addr_start;
            memcpy(reference_image, emulator_get_frame_buffer(emu), sizeof(FrameBuffer));
        } else {
            if (memcmp(reference_image, emulator_get_frame_buffer(emu), sizeof(FrameBuffer)) != 0) {
                char filename[32];
                sprintf(filename, "output/%s-%02x.%04x-%04x/%04x.bmp", typeToString[int(target_type)], target_bank, target_addr_start, target_addr_end, current_address);
                SDL_SaveBMP(backbuffer, filename);
            }
            current_address += 1;
            if (current_address == target_addr_end)
                run_state = RunState::Inactive;
        }
        emulator_delete(emu);
    }

    void draw(SDL_Surface* window_surface, int scale)
    {
        SDL_Rect window_rect{0, 0, 160*scale,144*scale};
        SDL_BlitScaled(backbuffer, nullptr, window_surface, &window_rect);
    }

    void updateStatus(InfoBar& infobar)
    {
        char line0[40];
        char line1[40];
        if (run_state != RunState::Inactive) {
            sprintf(line0, "Sweeping: %-4s %02x:%04x-%04x: %04x", typeToString[int(target_type)], target_bank, target_addr_start, target_addr_end, current_address);
            infobar.setStatus(line0, "");
            return;
        }
        sprintf(line0, "Target: %-4s %02x:%04x-%04x %-3s %02x", typeToString[int(target_type)], target_bank, target_addr_start, target_addr_end, modeToString[int(sweep_mode)], sweep_value);
        if (!isValid())
            sprintf(line1, "Target INVALID");
        else if (!main_emulator.hasSaveState())
            sprintf(line1, "Missing save state.");
        else
            sprintf(line1, "Ready: [Enter]");
        int cursor_x = -1;
        int cursor_y = 0;
        int cursor_width = 1;
        switch(cursor_pos) {
        case CursorPos::Type: cursor_x = 8; cursor_width = 4; break;
        case CursorPos::Bank0: cursor_x = 13; break;
        case CursorPos::Bank1: cursor_x = 14; break;
        case CursorPos::Start0: cursor_x = 16; break;
        case CursorPos::Start1: cursor_x = 17; break;
        case CursorPos::Start2: cursor_x = 18; break;
        case CursorPos::Start3: cursor_x = 19; break;
        case CursorPos::End0: cursor_x = 21; break;
        case CursorPos::End1: cursor_x = 22; break;
        case CursorPos::End2: cursor_x = 23; break;
        case CursorPos::End3: cursor_x = 24; break;
        case CursorPos::Mode: cursor_x = 26; cursor_width = 3; break;
        case CursorPos::Value0: cursor_x = 30; break;
        case CursorPos::Value1: cursor_x = 31; break;
        }

        infobar.setStatus(line0, line1, cursor_x, cursor_y, cursor_width);
    }

    bool isActive()
    {
        return run_state != RunState::Inactive;
    }

private:
    MainEmulator& main_emulator;
    FileData base_rom_file;
    FrameBuffer reference_image;

    bool isValid()
    {
        if (target_addr_end <= target_addr_start) return false;
        switch(target_type) {
        case TargetType::ROM:
            if (target_bank == 0) {
                if (target_addr_start > 0x4000) return false;
                if (target_addr_end > 0x4000) return false;
            } else {
                if (target_addr_start < 0x4000) return false;
                if (target_addr_end < 0x4000) return false;
                if (target_addr_start > 0x8000) return false;
                if (target_addr_end > 0x8000) return false;
            }
            break;
        case TargetType::WRAM:
            if (target_addr_start < 0xC000) return false;
            if (target_addr_start > 0xE000) return false;
            if (target_addr_end < 0xC000) return false;
            if (target_addr_end > 0xE000) return false;
            break;
        case TargetType::HRAM:
            if (target_addr_start < 0xFF80) return false;
            if (target_addr_start > 0xFF80) return false;
            if (target_addr_end < 0xFFFF) return false;
            if (target_addr_end > 0xFFFF) return false;
            break;
        }
        return true;
    }

    uint8_t applySweep(uint8_t value)
    {
        switch(sweep_mode) {
        case SweepMode::Set: return sweep_value;
        case SweepMode::Add: return value + sweep_value;
        case SweepMode::Sub: return value - sweep_value;
        case SweepMode::Xor: return value ^ sweep_value;
        }
        return value;
    }

    int getCurrent()
    {
        switch(cursor_pos) {
        case CursorPos::Type: return (int)target_type;
        case CursorPos::Bank0: return (target_bank >> 4) & 0x0F;
        case CursorPos::Bank1: return (target_bank >> 0) & 0x0F;
        case CursorPos::Start0: return (target_addr_start >> 12) & 0x0F;
        case CursorPos::Start1: return (target_addr_start >> 8) & 0x0F;
        case CursorPos::Start2: return (target_addr_start >> 4) & 0x0F;
        case CursorPos::Start3: return (target_addr_start >> 0) & 0x0F;
        case CursorPos::End0: return (target_addr_end >> 12) & 0x0F;
        case CursorPos::End1: return (target_addr_end >> 8) & 0x0F;
        case CursorPos::End2: return (target_addr_end >> 4) & 0x0F;
        case CursorPos::End3: return (target_addr_end >> 0) & 0x0F;
        case CursorPos::Mode: return int(sweep_mode);
        case CursorPos::Value0: return (sweep_value >> 4) & 0x0F;
        case CursorPos::Value1: return (sweep_value >> 0) & 0x0F;
        }
        return 0;
    }

    void setCurrent(int value)
    {
        switch(cursor_pos) {
        case CursorPos::Type: while(value < int(TargetType::ROM)) value += 3; while(value > int(TargetType::HRAM)) value -= 3; target_type = TargetType(value); break;
        case CursorPos::Bank0: target_bank = (target_bank & 0x0F) | ((value & 0x0F) << 4); break;
        case CursorPos::Bank1: target_bank = (target_bank & 0xF0) | ((value & 0x0F) << 0); break;
        case CursorPos::Start0: target_addr_start = (target_addr_start & 0x0FFF) | ((value & 0x0F) << 12); break;
        case CursorPos::Start1: target_addr_start = (target_addr_start & 0xF0FF) | ((value & 0x0F) << 8); break;
        case CursorPos::Start2: target_addr_start = (target_addr_start & 0xFF0F) | ((value & 0x0F) << 4); break;
        case CursorPos::Start3: target_addr_start = (target_addr_start & 0xFFF0) | ((value & 0x0F) << 0); break;
        case CursorPos::End0: target_addr_end = (target_addr_end & 0x0FFF) | ((value & 0x0F) << 12); break;
        case CursorPos::End1: target_addr_end = (target_addr_end & 0xF0FF) | ((value & 0x0F) << 8); break;
        case CursorPos::End2: target_addr_end = (target_addr_end & 0xFF0F) | ((value & 0x0F) << 4); break;
        case CursorPos::End3: target_addr_end = (target_addr_end & 0xFFF0) | ((value & 0x0F) << 0); break;
        case CursorPos::Mode: while(value < int(SweepMode::Set)) value += 4; while(value > int(SweepMode::Xor)) value -= 4; sweep_mode = SweepMode(value); break;
        case CursorPos::Value0: sweep_value = (sweep_value & 0x0F) | ((value & 0x0F) << 4); break;
        case CursorPos::Value1: sweep_value = (sweep_value & 0xF0) | ((value & 0x0F) << 0); break;
        }
    }

    SDL_Surface* backbuffer;

    enum class TargetType {
        ROM,
        WRAM,
        HRAM
    } target_type = TargetType::ROM;
    int target_bank = 0;
    int target_addr_start = 0;
    int target_addr_end = 0;
    enum class CursorPos {
        Type,
        Bank0, Bank1,
        Start0, Start1, Start2, Start3,
        End0, End1, End2, End3,
        Mode,
        Value0, Value1
    } cursor_pos = CursorPos::Type;
    enum class SweepMode
    {
        Set,
        Add,
        Sub,
        Xor
    } sweep_mode = SweepMode::Add;
    uint8_t sweep_value = 1;


    enum class RunState{
        Inactive,
        ReferenceImage,
        Sweeping
    } run_state = RunState::Inactive;
    int current_address = 0;

    static constexpr const char* typeToString[3] = {"ROM", "WRAM", "HRAM"};
    static constexpr const char* modeToString[4] = {"SET", "ADD", "SUB", "XOR"};
};

void printusage(const char* app)
{
    printf("Usage:\n");
    printf("%s rom.gb[c] [-S display_scale]\n", app);
}

int main(int argc, char** argv)
{
    std::string rom_filename;
    int scale = 3;
    int c;
    while((c = getopt(argc, argv, "-S:")) != -1)
    {
        switch(c)
        {
        case 1: rom_filename = optarg; break;
        case 'S': scale = std::max(1, atoi(optarg)); break;
        case '?':
            printusage(argv[0]);
            exit(0);
        }
    }

    if (rom_filename.empty()) {
        rom_filename = filedialog();
    }

    SDL_Init(SDL_INIT_EVERYTHING);
    auto window = SDL_CreateWindow("SweepEmu", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, SCREEN_WIDTH * scale, 160 * scale, SDL_WINDOW_SHOWN);
    auto window_surface = SDL_GetWindowSurface(window);

    MainEmulator main_emulator(rom_filename.c_str());
    if (!main_emulator.romLoaded())
        exit(1);
    InfoBar info_bar;
    Sweeper sweeper{main_emulator, rom_filename.c_str()};
    enum class Mode
    {
        Game, Sweeper
    } mode = Mode::Game;

    bool running = true;
    bool fast_forward = false;
    while(running) {
        SDL_Event e;
        while(SDL_PollEvent(&e)) {
            switch(e.type) {
                case SDL_KEYDOWN:
                    if (e.key.keysym.sym == SDLK_ESCAPE) running = false;
                    if (e.key.keysym.sym == SDLK_KP_PLUS) fast_forward = true;
                    if (e.key.keysym.sym == SDLK_TAB) mode = mode == Mode::Game ? Mode::Sweeper : Mode::Game;
                    if (mode == Mode::Game)
                        main_emulator.handleKey(e.key.keysym.sym, true);
                    else
                        sweeper.handleKey(e.key.keysym.sym, true);
                    break;
                case SDL_KEYUP:
                    if (e.key.keysym.sym == SDLK_KP_PLUS) fast_forward = false;
                    if (mode == Mode::Game)
                        main_emulator.handleKey(e.key.keysym.sym, false);
                    else
                        sweeper.handleKey(e.key.keysym.sym, false);
                    break;
                case SDL_QUIT: running = false; break;
            }
        }

        switch(mode)
        {
        case Mode::Game:
            info_bar.setStatus("[F2]: Load state [F4]: Save state", "[TAB]: Sweeper config");
            main_emulator.advanceFrame();
            main_emulator.draw(window_surface, scale);
            break;
        case Mode::Sweeper:
            sweeper.update();
            sweeper.updateStatus(info_bar);
            sweeper.draw(window_surface, scale);
            break;
        }
        info_bar.draw(window_surface, scale);

        SDL_UpdateWindowSurface(window);
        if (!sweeper.isActive() && !fast_forward)
            SDL_Delay(1000/60);
    }
    return 0;
}