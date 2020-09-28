import argparse

from rom import ROM
from disassembler import Disassembler
from instrumentation import processInstrumentation
from annotation import simple
from annotation import sdcc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=str)
    parser.add_argument("--instrumentation", action='append', default=[])
    parser.add_argument("--source")
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--plugin", action='append', default=[])
    args = parser.parse_args()

    for plugin in args.plugin:
        exec(open(plugin, "rt").read())

    rom = ROM(args.rom)
    disassembler = Disassembler(rom)
    disassembler.readSources(args.source if args.source else args.output)
    for instrumentation_file in args.instrumentation:
        processInstrumentation(instrumentation_file)
    disassembler.processRom()
    disassembler.export(args.output)
