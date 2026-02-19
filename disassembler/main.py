import argparse
import importlib.util
import os
import inspect
import textwrap
import itertools

from rom import ROM
from disassembler import Disassembler
from instrumentation import processInstrumentation
from annotation import annotation
from annotation import simple
from annotation import value
from annotation import sdcc



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=str, nargs="?")
    parser.add_argument("--wram-banks", type=int, default=1)
    parser.add_argument("--instrumentation", action='append', default=[])
    parser.add_argument("--source")
    parser.add_argument("--output", type=str, required=False)
    parser.add_argument("--plugin", action='append', default=[])
    parser.add_argument("--list-annotations", action="store_true")
    args = parser.parse_args()

    if not args.rom and not args.list_annotations:
        parser.print_help()
        exit(1)

    for plugin in args.plugin:
        if os.path.isdir(plugin):
            for f in sorted(os.listdir(plugin)):
                if f.endswith(".py"):
                    f = os.path.join(plugin, f)
                    spec = importlib.util.spec_from_file_location("plugin", f)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
        else:
            spec = importlib.util.spec_from_file_location("plugin", plugin)
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                print("Failed to load plugin: %s" % (plugin))

    if args.list_annotations:
        print("Available annotations:")
        for name, func in sorted(annotation.ALL_ANNOTATIONS.items()):
            sig = inspect.signature(func)
            usage_line = f";@{name}"
            for name, param in itertools.islice(sig.parameters.items(), 2, None):
                if param.kind != param.KEYWORD_ONLY:
                    usage_line += f" [{name}]"
                elif param.default == param.empty:
                    usage_line += f" {name}=..."
                elif param.default == None:
                    usage_line += f" [{name}=...]"
                else:
                    usage_line += f" [{name}={param.default}]"
            print(usage_line)
            doc = inspect.getdoc(func)
            if doc is not None:
                print(textwrap.indent(doc, "  "))
            print("")

    if args.rom:
        rom = ROM(args.rom)
        disassembler = Disassembler(rom, args.wram_banks)
        disassembler.readSources(args.source if args.source else args.output)
        for instrumentation_file in args.instrumentation:
            processInstrumentation(instrumentation_file)
        disassembler.processRom()
        if args.output:
            disassembler.export(args.output)
        else:
            print("Warning: no output folder specified. Not generating output")
