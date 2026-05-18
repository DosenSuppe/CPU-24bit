"""Main assembler implementation."""

import os
import re

from typing import List
from CompilerComponents.RelocatableObject import RelocatableObject
from CompilerComponents.OperandParser import OperandParser
from CompilerComponents.InstructionCompiler import (
    SimpleInstructionCompiler,
    MovInstructionCompiler,
    ALUInstructionCompiler,
    CMPInstructionCompiler,
    LDIInstructionCompiler,
    STRInstructionCompiler,
    LDR_LOCInstructionCompiler,
    STR_LOCInstructionCompiler,
    LDR_ARGInstructionCompiler,
    STR_ARGInstructionCompiler,
    SET_SP_RInstructionCompiler,
    ControlFlowInstructionCompiler,
    StackInstructionCompiler,
    SystemInstructionCompiler
)
from CompilerComponents.InstructionSet import (
    SIMPLE_INSTRUCTIONS,
    ALU_BINARY_OPERATIONS,
    ALU_UNARY_OPERATIONS,
    CONTROL_FLOW_INSTRUCTIONS
)
from CompilerComponents.Exceptions import SyntaxError, SegmentError, InstructionError


class Assembler:
    """
    Main assembler class for compiling assembly code to relocatable objects.
    
    The assembler processes assembly source code and generates relocatable
    object files containing bytecode, labels, and relocation information.
    """
    
    def __init__(self, pInstructionSet: dict, pRegisters, pSourceDir: str = '.'):
        """
        Initialize the assembler.
        
        Args:
            instruction_set: Dictionary of instruction mnemonics to opcodes
            registers: Register class with register definitions
            source_dir: Base directory for resolving import paths
        """
        self.instructionSet = pInstructionSet
        self.registers = pRegisters
        self.sourceDir = pSourceDir
        self.operandParser = OperandParser(pRegisters)
    
    def Compile(self, pSourceCode: str, pFilename: str) -> RelocatableObject:
        """
        Compile assembly code into a relocatable object file.
        
        Args:
            assembly_code: Assembly source code as string
            filename: Source filename for reference
            
        Returns:
            RelocatableObject containing compiled segments and metadata
            
        Raises:
            SyntaxError: If assembly syntax is invalid
            SegmentError: If segment usage is invalid
            InstructionError: If instruction format is invalid
        """
        obj = RelocatableObject(pFilename)
        lines = pSourceCode.split('\n')
        
        # First pass: collect imports
        self._ProcessImports(lines, obj)
        
        # Second pass: compile instructions and labels
        self._CompileLines(lines, obj)
        
        return obj
    
    def _ProcessImports(self, pLines: List[str], pRelocatableObject: RelocatableObject) -> None:
        """Process import and declare directives."""
        for line in pLines:
            cleanLine = self._CleanLine(line)
            if not cleanLine:
                continue
            
            if cleanLine.upper().startswith('!IMPORT'):
                match = re.match(
                    r'!IMPORT\s+(["\']?)([^"\']+)\1(?:\s+AS\s+(\S+))?',
                    cleanLine,
                    re.IGNORECASE
                )
                if match:
                    import_file = match.group(2)
                    alias = match.group(3)
                    pRelocatableObject.AddImport(import_file, alias)
            
            elif cleanLine.upper().startswith('!DECLARE'):
                # Parse: !DECLARE VariableName = expression
                match = re.match(
                    r'!DECLARE\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)',
                    cleanLine,
                    re.IGNORECASE
                )
                if match:
                    var_name = match.group(1)
                    expression = match.group(2).strip()
                    pRelocatableObject.AddDeclaration(var_name, expression)
    
    def _CompileLines(self, pLines: List[str], pRelocatableObject: RelocatableObject) -> None:
        """Compile assembly lines into bytecode."""
        currentSegment = None
        
        for lineNum, line in enumerate(pLines, 1):
            cleanLine = self._CleanLine(line)
            if not cleanLine:
                continue
            
            try:
                # Segment directive
                if cleanLine.startswith('.'):
                    currentSegment = self._ProcessSegment(cleanLine, pRelocatableObject)
                    continue
                
                # Import directive (skip, already processed)
                if cleanLine.upper().startswith('!IMPORT'):
                    continue
                
                # Declare directive (skip, already processed)
                if cleanLine.upper().startswith('!DECLARE'):
                    continue
                
                # Label definition
                if cleanLine.endswith(':'):
                    self._ProcessLabel(cleanLine, currentSegment, pRelocatableObject, lineNum)
                    continue
                
                # Data word directive
                if cleanLine.upper().startswith('DW ') or cleanLine.upper() == 'DW':
                    if currentSegment is None:
                        raise SegmentError(
                            f"DW directive outside any segment: {cleanLine}",
                            lineNum
                        )
                    self._ProcessDataWord(cleanLine, currentSegment, pRelocatableObject, lineNum)
                    continue
                
                # Include binary file directive
                if cleanLine.upper().startswith('INCBIN ') or cleanLine.upper().startswith('INCBIN\t'):
                    if currentSegment is None:
                        raise SegmentError(
                            f"INCBIN directive outside any segment: {cleanLine}",
                            lineNum
                        )
                    self._ProcessIncBin(cleanLine, currentSegment, pRelocatableObject, lineNum)
                    continue
                
                # Instruction
                if currentSegment is None:
                    raise SegmentError(
                        f"Instruction outside any segment: {cleanLine}",
                        lineNum
                    )
                
                self._CompileInstruction(cleanLine, currentSegment, pRelocatableObject, lineNum)
                
            except (SyntaxError, SegmentError, InstructionError) as e:
                # Re-raise with line number if not already set
                if not hasattr(e, 'lineNumber') or e.lineNumber is None:
                    raise type(e)(str(e), lineNum)
                raise
            except Exception as e:
                raise SyntaxError(f"{e}", lineNum)
    
    def _CleanLine(self, line: str) -> str:
        """Remove comments and whitespace from a line."""
        if ';' in line:
            line = line[:line.find(';')]
            
        if ('@' in line):
            line = line[:line.find('@')]
            
        return line.strip()
    
    def _ProcessSegment(self, pLine: str, pRelocatableObject: RelocatableObject) -> str:
        """Process a segment directive."""
        segmentName = pLine[1:].strip()
        pRelocatableObject.EnsureSegment(segmentName)
        return segmentName
    
    def _ProcessLabel(self, pLine: str, currentSegment: str, pRelocatableObject: RelocatableObject, lineNum: int) -> None:
        """Process a label definition."""
        if currentSegment is None:
            raise SegmentError(
                f"Label '{pLine[:-1]}' defined outside any segment",
                lineNum
            )
        
        labelName = pLine[:-1].strip()
        offset = pRelocatableObject.GetSegmentOffset(currentSegment)
        pRelocatableObject.AddLabel(labelName, currentSegment, offset)
    
    def _ProcessDataWord(self, pLine: str, pSegment: str, pRelocatableObject: RelocatableObject, lineNum: int) -> None:
        """
        Process a DW (Define Word) directive to emit raw 24-bit data values.
        
        Syntax:
            DW #0xFF              ; immediate value
            DW 0xFF               ; plain number
            DW #1, #2, #3         ; multiple values
            DW MyLabel             ; symbol reference (creates relocation)
            DW $VideoDisplay.Start ; memory config reference (creates relocation)
        """
        parts = pLine.split(maxsplit=1)
        if len(parts) < 2:
            raise SyntaxError("DW requires at least one value", lineNum)
        
        values = [v.strip() for v in parts[1].split(',')]
        for val in values:
            if not val:
                raise SyntaxError("Empty value in DW directive", lineNum)
            
            if val.startswith('#'):
                # Immediate value with # prefix
                numStr = val[1:].strip()
                try:
                    number = int(numStr, 0)
                except ValueError:
                    raise SyntaxError(f"Invalid number in DW: {val}", lineNum)
                pRelocatableObject.AppendToSegment(pSegment, number & 0xFFFFFF)
            
            elif val.startswith('$'):
                # Memory config symbol reference
                offset = pRelocatableObject.GetSegmentOffset(pSegment)
                pRelocatableObject.AppendToSegment(pSegment, 0)
                symbol = f"$MEM${val[1:]}"
                pRelocatableObject.AddRelocation(pSegment, offset, symbol, 'absolute')
            
            elif val[0].isdigit():
                # Plain number (no # prefix)
                try:
                    number = int(val, 0)
                except ValueError:
                    raise SyntaxError(f"Invalid number in DW: {val}", lineNum)
                pRelocatableObject.AppendToSegment(pSegment, number & 0xFFFFFF)
            
            else:
                # Symbol/label reference
                offset = pRelocatableObject.GetSegmentOffset(pSegment)
                pRelocatableObject.AppendToSegment(pSegment, 0)
                pRelocatableObject.AddRelocation(pSegment, offset, val, 'absolute')
    
    def _ProcessIncBin(self, pLine: str, pSegment: str, pRelocatableObject: RelocatableObject, lineNum: int) -> None:
        """
        Process an INCBIN directive to include a binary file as data words.
        
        Each byte in the file becomes one 24-bit word (zero-extended).
        This is ideal for image pixel data where each byte is a color index.
        
        Syntax:
            INCBIN "path/to/file.bin"
        """
        match = re.match(r'INCBIN\s+["\']([^"\']+)["\']', pLine, re.IGNORECASE)
        if not match:
            raise SyntaxError("INCBIN requires a quoted filename: INCBIN \"file.bin\"", lineNum)
        
        filename = match.group(1)
        # Resolve relative to source directory
        filepath = os.path.join(self.sourceDir, filename)
        
        if not os.path.isfile(filepath):
            raise SyntaxError(f"INCBIN file not found: {filepath}", lineNum)
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
        except IOError as e:
            raise SyntaxError(f"INCBIN could not read file: {e}", lineNum)
        
        for byte in data:
            pRelocatableObject.AppendToSegment(pSegment, byte & 0xFFFFFF)
    
    def _CompileInstruction(self, line: str, segment: str, 
                            pRelocatableObject: RelocatableObject, lineNum: int) -> None:
        """Compile a single instruction line."""
        # Parse mnemonic and operands
        parts = line.split(maxsplit=1)
        mnemonic = parts[0].upper()
        
        if mnemonic not in self.instructionSet:
            raise InstructionError(f"Unknown instruction: {mnemonic}", lineNum)
        
        # Parse operands
        operandStrings = []
        if len(parts) > 1:
            operandStrings = [op.strip() for op in parts[1].split(',')]
        
        parsedOperands = []
        for op_str in operandStrings:
            parsedOperands.append(self.operandParser.ParseOperand(op_str))
        
        # Get current offset before compilation
        offset = pRelocatableObject.GetSegmentOffset(segment)
        
        # Compile based on instruction type
        result = self._DispatchInstructionCompiler(
            mnemonic, parsedOperands, segment, offset
        )
        
        # Add bytecode to segment
        pRelocatableObject.AppendToSegment(segment, result.bytecode)
        
        # Add extra word if present
        if result.extraWord is not None:
            pRelocatableObject.AppendToSegment(segment, result.extraWord)
        
        # Add relocation if present
        if result.relocation:
            pRelocatableObject.relocations.append(result.relocation)
    
    def _DispatchInstructionCompiler(self, pMnemonic: str, pOperands: list,
                                      pSegment: str, pOffset: int):
        """Dispatch to appropriate instruction compiler."""
        
        # Simple instructions
        if pMnemonic in SIMPLE_INSTRUCTIONS:
            return SimpleInstructionCompiler.Compile(pMnemonic)
        
        # MOV instruction
        elif pMnemonic == 'MOV':
            return MovInstructionCompiler.Compile(pOperands)
        
        # Binary ALU operations
        elif pMnemonic in ALU_BINARY_OPERATIONS:
            return ALUInstructionCompiler.CompileBinary(pMnemonic, pOperands)
        
        # Unary ALU operations
        elif pMnemonic in ALU_UNARY_OPERATIONS:
            return ALUInstructionCompiler.CompileUnary(pMnemonic, pOperands)
        
        # CMP instruction
        elif pMnemonic == 'CMP':
            return CMPInstructionCompiler.Compile(pOperands)
        
        # LDI instruction
        elif pMnemonic == 'LDI':
            return LDIInstructionCompiler.Compile(pOperands, pSegment, pOffset)
        
        # STR instruction
        elif pMnemonic == 'STR':
            return STRInstructionCompiler.Compile(pOperands, pSegment, pOffset)

        # Frame-pointer-relative load/store (locals at FP-N, args at FP+N)
        elif pMnemonic == 'LDR_LOC':
            return LDR_LOCInstructionCompiler.Compile(pOperands, pSegment, pOffset)
        elif pMnemonic == 'STR_LOC':
            return STR_LOCInstructionCompiler.Compile(pOperands, pSegment, pOffset)
        elif pMnemonic == 'LDR_ARG':
            return LDR_ARGInstructionCompiler.Compile(pOperands, pSegment, pOffset)
        elif pMnemonic == 'STR_ARG':
            return STR_ARGInstructionCompiler.Compile(pOperands, pSegment, pOffset)
        elif pMnemonic == 'SET_SP_R':
            return SET_SP_RInstructionCompiler.Compile(pOperands, pSegment, pOffset)

        # Control flow instructions
        elif pMnemonic in CONTROL_FLOW_INSTRUCTIONS:
            return ControlFlowInstructionCompiler.Compile(
                pMnemonic, pOperands, pSegment, pOffset
            )
        
        # Stack instructions
        elif pMnemonic == 'PUSH':
            return StackInstructionCompiler.CompilePush(pOperands, pSegment, pOffset)
        elif pMnemonic == 'POP':
            return StackInstructionCompiler.CompilePop(pOperands)
        
        # System instructions
        elif pMnemonic == 'SET_SP':
            return SystemInstructionCompiler.CompileSetSP(pOperands, pSegment, pOffset)
        elif pMnemonic == 'GET_SP':
            return SystemInstructionCompiler.CompileGetSP(pOperands)
        elif pMnemonic == 'GET_PC':
            return SystemInstructionCompiler.CompileGetPC(pOperands)
        elif pMnemonic == 'SET_IVR':
            return SystemInstructionCompiler.CompileSetIVR(pOperands, pSegment, pOffset)
        elif pMnemonic == 'GET_INT_ID':
            return SystemInstructionCompiler.CompileGetIntID(pOperands)
        
        else:
            raise InstructionError(f"Unsupported instruction: {pMnemonic}")