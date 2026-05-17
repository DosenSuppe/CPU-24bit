"""
C-to-DASM compiler for the 24-bit CPU.

Compiles a C subset (int/char/pointers/arrays/functions/if/while/return,
inline asm, syscall builtin) to DASM assembly that can be fed to Compiler.py
and then linked with Linker.py.

Usage:
    python cc.py <input.c> [-o <output.asm>] [--no-entry]

Flags:
    -o <path>    Output path (default: <input>.asm)
    --no-entry   Suppress the .Kernel boot stub. Use when the file is meant
                 to be linked as a library — i.e., something else is providing
                 the entry point. Without this flag, any file defining `main`
                 emits a .Kernel segment with SET_SP/SET_IVR/CALL main/HALT,
                 which collides if multiple such objects are linked together.

Example:
    python cc.py examples/add.c -o examples/add.asm
    python Compiler.py examples/add.asm
    python Linker.py bin/examples/add.obj mem.cfg add.o
"""

import os
import sys

from CCompilerComponents.Lexer import Lexer
from CCompilerComponents.Parser import Parser
from CCompilerComponents.Preprocessor import Preprocess
from CCompilerComponents.SemanticAnalyzer import SemanticAnalyzer
from CCompilerComponents.CodeGen import CodeGen
from CCompilerComponents.Exceptions import CCompileError


def CompileFile(pInputPath: str, pOutputPath: str = None, pNoEntry: bool = False) -> str:
    """Compile a C source file to DASM. Returns the output path written."""
    source = Preprocess(pInputPath)

    base_name = os.path.basename(pInputPath)

    lexer = Lexer(source)
    tokens = lexer.Tokenize()

    parser = Parser(tokens)
    unit = parser.Parse()

    analyzer = SemanticAnalyzer()
    analyzer.Analyze(unit)

    codegen = CodeGen(analyzer, base_name)
    codegen.no_entry = pNoEntry
    asm_text = codegen.Generate(unit)

    if pOutputPath is None:
        if pInputPath.endswith(".c"):
            pOutputPath = pInputPath[:-2] + ".asm"
        else:
            pOutputPath = pInputPath + ".asm"

    with open(pOutputPath, "w") as f:
        f.write(asm_text)

    return pOutputPath


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if args else 1)

    input_path = None
    output_path = None
    no_entry = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "-o":
            if i + 1 >= len(args):
                print("Error: -o requires an argument")
                sys.exit(1)
            output_path = args[i + 1]
            i += 2
        elif a == "--no-entry":
            no_entry = True
            i += 1
        elif a.startswith("-"):
            print(f"Error: unknown flag {a!r}")
            sys.exit(1)
        else:
            if input_path is not None:
                print("Error: multiple input files not supported")
                sys.exit(1)
            input_path = a
            i += 1

    if input_path is None:
        print("Error: missing input file")
        print(__doc__)
        sys.exit(1)

    try:
        result = CompileFile(input_path, output_path, no_entry)
    except CCompileError as e:
        print(f"cc: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"cc: file not found: {e.filename}")
        sys.exit(1)

    print(f"Wrote {result}")


if __name__ == "__main__":
    main()
