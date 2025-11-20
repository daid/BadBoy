#include "platform.h"

#include <sys/stat.h>
#include <string>

#ifdef _WIN32
#include <windows.h>

void makedir(const char* path) { mkdir(path); }
std::string filedialog()
{
    char filter_string[] = "Gameboy roms\0*.gb;*.gbc\0";

    OPENFILENAMEA openfilename;
    char filename[MAX_PATH];
    memset(&openfilename, 0, sizeof(openfilename));
    memset(&filename, 0, sizeof(filename));

    openfilename.lStructSize = sizeof(openfilename);
    openfilename.lpstrFilter = filter_string;
    openfilename.lpstrFile = filename;
    openfilename.nMaxFile = sizeof(filename);
    openfilename.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;

    GetOpenFileNameA(&openfilename);
    return filename;
}
#else
void makedir(const char* path) { mkdir(path, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH); }
std::string filedialog() { return ""; }
#endif