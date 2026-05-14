"""
Assembly compiler for 24-bit CPU.

This is the main entry point for the assembler. It compiles assembly source
files (.asm) into relocatable object files (.obj) that can be linked together.

By default the compiler follows all !IMPORT directives recursively and compiles
every dependency in one pass, so you only need to invoke it on the top-level
entry file.

Usage:
    python Compiler.py <input.asm> [output_base_name]

Example:
    python Compiler.py os/src/main.asm
    -> compiles main.asm and every file it imports (recursively)
    -> outputs to os/bin/main.obj, os/bin/drivers/TTYDriver.obj, ...
"""

import sys
import json
import os

from CompilerComponents.Assembler import Assembler
from CompilerComponents.InstructionSet import INSTRUCTION_SET
from Values.Registers import Register
from CompilerComponents.OutputResolver import OutputPathResolver
from CompilerComponents.Exceptions import AssemblerError


def _CompileOne(absPath: str, outputOverride: str = None) -> tuple:
    """
    Compile a single file.  Returns (obj, finalOutputPath).
    Exits on any error so callers don't have to handle None.
    """
    sourceDir = os.path.dirname(absPath)
    assembler = Assembler(INSTRUCTION_SET, Register, sourceDir)

    try:
        with open(absPath, 'r') as f:
            sourceCode = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {absPath}")
        sys.exit(1)

    try:
        obj = assembler.Compile(sourceCode, absPath)
    except AssemblerError as e:
        print(f"Assembly error in {os.path.basename(absPath)}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error in {os.path.basename(absPath)}: {e}")
        sys.exit(1)

    finalOutput = OutputPathResolver.ResolveOutputPath(absPath, outputOverride)
    with open(finalOutput + ".obj", 'w') as f:
        json.dump(obj.ToDict(), f, indent=2)

    return obj, finalOutput


def CompileWithDependencies(pEntryFile: str, pOutputFile: str = None) -> None:
    """
    Compile an assembly file and all files it imports, recursively.

    Each source file produces one .obj file.  Circular imports are detected
    and reported as warnings rather than infinite loops.

    Args:
        pEntryFile:  Path to the top-level assembly file.
        pOutputFile: Optional output path override for the entry file only
                     (without .obj extension).  Imported files always use the
                     auto-resolved output path.
    """
    entryAbs = os.path.abspath(pEntryFile)

    compiled: set  = set()   # abs paths fully compiled and written
    visiting: set  = set()   # abs paths currently on the DFS call stack
    results:  list = []      # (inputAbs, outputPath) in compilation order

    def _recurse(absPath: str, outputOverride: str = None) -> None:
        if absPath in compiled:
            return
        if absPath in visiting:
            print(f"Warning: Circular import detected, skipping: {absPath}")
            return

        visiting.add(absPath)

        # Compile this file first so we can read its imports list.
        obj, finalOutput = _CompileOne(absPath, outputOverride)

        # Recurse into each import before recording this file as done.
        sourceDir = os.path.dirname(absPath)
        for importRelPath in obj.imports:
            importAbs = os.path.normpath(os.path.join(sourceDir, importRelPath))
            _recurse(importAbs)

        visiting.discard(absPath)
        compiled.add(absPath)
        results.append((absPath, finalOutput))

    _recurse(entryAbs, pOutputFile)

    # Summary
    print(f"\nCompiled {len(results)} file(s):")
    for src, out in results:
        print(f"  {src}")
        print(f"  -> {out}.obj")


def CompileFile(pInputFile: str, pOutputFile: str = None) -> None:
    """Compile a single assembly file (no dependency following)."""
    obj, finalOutput = _CompileOne(os.path.abspath(pInputFile), pOutputFile)
    print(f"Object file generated: {finalOutput}.obj")
    print(f"Segments: {list(obj.segments.keys())}")
    print(f"Labels: {len(obj.labels)}")
    print(f"Relocations: {len(obj.relocations)}")


def main():
    """Main entry point for CLI."""
    if len(sys.argv) < 2:
        print("Usage: python Compiler.py <input.asm> [output_base_name]")
        print("Compiles the given file and all its !IMPORT dependencies recursively.")
        print("")
        print("Example:")
        print("  python Compiler.py os/src/main.asm")
        print("  -> os/bin/main.obj, os/bin/drivers/TTYDriver.obj, ...")
        sys.exit(1)

    inputFile = sys.argv[1]
    outputFile = sys.argv[2] if len(sys.argv) > 2 else None

    CompileWithDependencies(inputFile, outputFile)


if __name__ == '__main__':
    main()
