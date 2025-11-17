"""
Assembly compiler for 24-bit CPU.

This is the main entry point for the assembler. It compiles assembly source
files (.asm) into relocatable object files (.obj) that can be linked together.

Usage:
    python Compiler.py <input.asm> [output_base_name]
    
Example:
    python Compiler.py os/src/drivers/JoystickDriver.asm
    -> outputs to os/bin/drivers/JoystickDriver.obj
"""

import sys
import json

from CompilerComponents.Assembler import Assembler
from CompilerComponents.InstructionSet import INSTRUCTION_SET
from Values.Registers import Register
from CompilerComponents.OutputResolver import OutputPathResolver
from CompilerComponents.Exceptions import AssemblerError


def CompileFile(pInputFile: str, pOutputFile: str = None) -> None:
    """
    Compile an assembly file to a relocatable object file.
    
    Args:
        input_file: Path to input assembly file
        output_file: Optional output path (without .obj extension)
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        AssemblerError: If compilation fails
    """
    # Create assembler instance
    assembler = Assembler(INSTRUCTION_SET, Register)
    
    try:
        with open(pInputFile, 'r') as f:
            sourceCode = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found: {pInputFile}")
        sys.exit(1)
    
    try:
        obj = assembler.Compile(sourceCode, pInputFile)
    except AssemblerError as e:
        print(f"Assembly failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during assembly: {e}")
        sys.exit(1)
    
    # Resolve output path
    finalOutput = OutputPathResolver.ResolveOutputPath(pInputFile, pOutputFile)
    
    # Write object file
    with open(finalOutput + ".obj", 'w') as f:
        json.dump(obj.ToDict(), f, indent=2)
    
    # Print summary
    print(f"Object file generated: {finalOutput}.obj")
    print(f"Segments: {list(obj.segments.keys())}")
    print(f"Labels: {len(obj.labels)}")
    print(f"Relocations: {len(obj.relocations)}")


def main():
    """Main entry point for CLI."""
    if len(sys.argv) < 2:
        print("Usage: python Compiler.py <input.asm> [output_base_name]")
        print("If output_base_name is not provided, directory structure will be auto-determined from input path")
        print("Example: python Compiler.py os/src/drivers/JoystickDriver.asm")
        print("         -> outputs to os/bin/drivers/JoystickDriver.obj")
        sys.exit(1)
    
    inputFile = sys.argv[1]
    outputFile = sys.argv[2] if len(sys.argv) > 2 else None
    
    CompileFile(inputFile, outputFile)


if __name__ == '__main__':
    main()
    