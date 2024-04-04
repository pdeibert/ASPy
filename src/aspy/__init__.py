__version__ = "0.0.0.dev0"
__author__ = "Philipp Deibert"

from .debug import debug  # noqa


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="ASPy",
        description="Parser & grounder for the ASPCore2 input language",
    )
    parser.add_argument("command", choices=["init", "ground"])
    parser.add_argument("-f", "--file", type=str, default=None)
    parser.add_argument("-o", "--outfile", type=str, default=None)

    # parse command line arguments
    args = parser.parse_args()

    if args.command == "init":
        if args.file is not None:
            print("Invalid option '-f'/'--file' for command 'init'")
            sys.exit(1)
        elif args.outfile is not None:
            print("Invalid option '-o'/'--outfile' for command 'init'")
            sys.exit(1)

        import os
        import pathlib

        # generate parser files
        os.system(
            f"antlr4 -Dlanguage=Python3 -visitor -no-listener {pathlib.Path(__file__).parent.resolve()}/parser/ASPCore2.g4"
        )
    elif args.command == "ground":
        if args.file is None:
            print("Missing value for option '-f'/'--file' for command 'ground'")
            sys.exit(1)

        from .grounding import Grounder
        from .program import Program

        # read input
        with open(args.file, "r") as f:
            prog = Program.from_string(f.read())

        # ground program
        ground_prog = Grounder(prog).ground()

        if args.outfile is None:
            # output ground program to console
            print(ground_prog)
        else:
            # write ground program to specified output file
            with open(args.outfile, "w") as f:
                f.write(str(ground_prog))
    else:
        print(f"Invalid command '{args.command}'")
        sys.exit(1)

    sys.exit(0)
