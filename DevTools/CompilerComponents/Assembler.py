"""Main assembler implementation."""

import re

from typing import List
from CompilerComponents.RelocatableObject import RelocatableObject
from CompilerComponents.OperandParser import OperandParser
from CompilerComponents.InstructionCompiler import (
    SimpleInstructionCompiler,
    MovInstructionCompiler,
    ALUInstructionCompiler,
    LDIInstructionCompiler,
    STRInstructionCompiler,
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
                    pRelocatableObject.AddImport(import_file)
            
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
        
        # LDI instruction
        elif pMnemonic == 'LDI':
            return LDIInstructionCompiler.Compile(pOperands, pSegment, pOffset)
        
        # STR instruction
        elif pMnemonic == 'STR':
            return STRInstructionCompiler.Compile(pOperands, pSegment, pOffset)
        
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
        elif pMnemonic == 'GET_INT_DATA':
            return SystemInstructionCompiler.CompileGetIntData(pOperands)
        
        else:
            raise InstructionError(f"Unsupported instruction: {pMnemonic}")