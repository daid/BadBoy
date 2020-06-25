import tokenize
import html
import os
import re


class XRefGenerator:
    def __init__(self):
        self.files = {}
        self.symbols = {}

        self.include_paths = ["src"]

    def load(self, filename):
        if not os.path.exists(filename):
            for include_path in self.include_paths:
                if os.path.exists(os.path.join(include_path, filename)):
                    filename = os.path.join(include_path, filename)
                    break
        if not os.path.exists(filename):
            return

        self.files[filename] = open(filename, "rt").readlines()
        for index, line in enumerate(self.files[filename]):
            m = re.match("([A-Za-z_\\.][A-Za-z_0-9\\.]+)\\:", line)
            if m:
                symbol = m.group(1)
                if symbol.startswith("."):
                    symbol = last_symbol + symbol
                else:
                    last_symbol = symbol
                self.symbols[symbol] = (filename, index)
            m = re.match("([A-Za-z_\\.][A-Za-z_0-9\\.]+) +EQU +\\$([A-Fa-f0-9]+)", line)
            if m:
                self.symbols[m.group(1)] = (filename, index)
            m = re.match("include \"([^\"]*)\"", line)
            if m:
                self.load(m.group(1))

    def export(self, target):
        f = open(target, "wt")
        f.write("""
<html>
<head>
<style>
.code {
    font-family: SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace;
    font-size: 12px;
    white-space: pre;
}
</style>
</head>
<body>""")
        for filename, lines in self.files.items():
            f.write("<table>")
            for index, line in enumerate(lines):
                f.write("<tr><td id='%s_%d' class='code'><a href='#%s_%d'>%d</a><td class='code'>" % (filename, index, filename, index, index + 1))
                f.write(self.formatCode(line))
            f.write("</table>")
        f.write("""</body></html>""")

    def formatCode(self, line):
        line = html.escape(line)
        for m in re.finditer("[A-Za-z_\\.][A-Za-z_0-9\\.]+", line):
            if m.group(0) in self.symbols:
                s = self.symbols[m.group(0)]
                line = line.replace(m.group(0), "<a href='#%s_%d'>%s</a>" % (s[0], s[1], m.group(0)))
        return line

if __name__ == "__main__":
    import sys
    xref = XRefGenerator()
    xref.load(sys.argv[1])
    xref.export(sys.argv[2])
