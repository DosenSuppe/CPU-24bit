import re
import sys
import os
import json
from Values.Registers import *
from typing import Dict, List, Tuple, Any

# --- Utility Functions ---
def GenerateSourceRegister(pRegister: int) -> int:
    return (pRegister & 0x1F) << 8

def GenerateDestinationRegister(pRegister: int) -> int:
    return (pRegister & 0x1F) << 13

# --- Instruction Set ---
INSTRUCTION_SET = {
    'NOP': 0x00, 
    'HALT': 0x01,
    'MOV': 0x02, 
    'LDI': [0x03, 0x04, 0x18], 
    'STR': [0x05, 0x06],
    'ADD': 0x07,
    'SUB': 0x08,
    'MUL': 0x09,
    'DIV': 0x0A, 
    'SHL': 0x0B,
    'AND': 0x0C,
    'OR': 0x0D,
    'XOR': 0x0E,
    'JP': [0x0F, 0x10],
    'JPZ': [0x11, 0x12],
    'JPC': [0x13, 0x14],
    'CALL': [0x15, 0x16],
    'RTS': 0x17
}

# --- Relocatable Object File Format ---
class RelocatableObject:
    """Represents a compiled object file with relocation info."""
    def __init__(self, filename: str):
        self.filename = filename
        self.segments: Dict[str, List[int]] = {}  # segment_name -> [bytecode words]
        self.labels: Dict[str, Tuple[str, int]] = {}  # label -> (segment, offset)
        self.relocations: List[Dict[str, Any]] = []  # [{segment, offset, type, symbol}]
        self.imports: List[str] = []  # list of imported files
        
    def to_dict(self) -> dict:
        return {
            'filename': self.filename,
            'segments': self.segments,
            'labels': self.labels,
            'relocations': self.relocations,
            'imports': self.imports
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'RelocatableObject':
        obj = RelocatableObject(data['filename'])
        obj.segments = data['segments']
        obj.labels = data['labels']
        obj.relocations = data['relocations']
        obj.imports = data['imports']
        return obj

# --- Assembler Class ---
class Assembler:
    def __init__(self, pInstructionSet, pRegisters, pPortRegisters, pSourceDir='.'):
        self.InstructionSet = pInstructionSet
        self.Registers = pRegisters
        self.PortRegisters = pPortRegisters
        self.SourceDir = pSourceDir
        
    def ParseRegister(self, pToken: str) -> int:
        return getattr(self.Registers, pToken.upper())
        
    def ParsePortRegister(self, pToken: str) -> int:
        return getattr(self.PortRegisters, pToken.upper())
    
    def IsRegister(self, pToken: str) -> bool:
        return hasattr(self.Registers, pToken.upper()) or hasattr(self.PortRegisters, pToken.upper())

    def ParseOperand(self, pOperand: str):
        pOperand = pOperand.strip()
        if pOperand.startswith('#'):
            try: return 'immediate', int(pOperand[1:], 0)
            except ValueError: raise ValueError(f"Invalid immediate value: {pOperand}")
        elif pOperand.startswith('[') and pOperand.endswith(']'):
            addressStr = pOperand[1:-1].strip()
            try: 
                if (self.IsRegister(addressStr)):
                    return 'register', self.ParseRegister(addressStr)
                
                if (addressStr.startswith('#')):
                    addressStr = addressStr[1:]
                
                return 'direct_address', int(addressStr, 0)
            except ValueError: raise ValueError(f"Invalid direct address: {pOperand}")
        elif hasattr(self.Registers, pOperand.upper()):
            return 'register', self.ParseRegister(pOperand)
        elif hasattr(self.PortRegisters, pOperand.upper()):
            return 'register', self.ParsePortRegister(pOperand)
        elif re.match(r'^[A-Z_][A-Z0-9_.]*$', pOperand.upper()):
            return 'symbol', pOperand.upper()
        else:
            raise ValueError(f"Unrecognized operand format: {pOperand}")

    def Compile(self, assembly_code: str, filename: str) -> RelocatableObject:
        """
        Compiles assembly code into a relocatable object file.
        Returns a RelocatableObject with segments, labels, and relocations.
        """
        obj = RelocatableObject(filename)
        
        lines = assembly_code.split('\n')
        current_segment = None
        segment_offset = 0  # offset within current segment
        import_namespaces = {}  # maps import_file -> namespace
        
        # First pass: collect import namespaces
        for line in lines:
            if ';' in line:
                line = line[:line.find(';')]
            line = line.strip()
            if not line:
                continue
            
            if line.upper().startswith('!IMPORT'):
                match = re.match(r'!IMPORT\s+(\S+)(?:\s+AS\s+(\S+))?', line, re.IGNORECASE)
                if match:
                    import_file = match.group(1)
                    namespace = match.group(2).upper() if match.group(2) else os.path.basename(import_file).replace('.asm', '').upper()
                    import_namespaces[import_file] = namespace
        
        # Second pass: compile
        for line_num, line in enumerate(lines, 1):
            # Cleanup
            if ';' in line:
                line = line[:line.find(';')]
            line = line.strip()
            if not line:
                continue
            
            # Check for segment declaration
            if line.startswith('.'):
                current_segment = line[1:].strip().upper()
                if current_segment not in obj.segments:
                    obj.segments[current_segment] = []
                segment_offset = len(obj.segments[current_segment])
                continue
            
            # Check for import directive
            if line.upper().startswith('!IMPORT'):
                match = re.match(r'!IMPORT\s+(\S+)(?:\s+AS\s+(\S+))?', line, re.IGNORECASE)
                if match:
                    import_file = match.group(1)
                    obj.imports.append(import_file)
                continue
            
            # Check for label definition
            if line.endswith(':'):
                if current_segment is None:
                    raise SyntaxError(f"Line {line_num}: Label '{line[:-1]}' defined outside any segment")
                label_name = line[:-1].strip().upper()
                obj.labels[label_name] = (current_segment, segment_offset)
                continue
            
            # Must be in a segment to compile instructions
            if current_segment is None:
                raise SyntaxError(f"Line {line_num}: Instruction outside any segment: {line}")
            
            # Compile instruction
            try:
                bytecode_word, extra_word, relocation = self._compile_instruction(
                    line, current_segment, segment_offset
                )
                
                obj.segments[current_segment].append(bytecode_word)
                segment_offset += 1
                
                if extra_word is not None:
                    obj.segments[current_segment].append(extra_word)
                    segment_offset += 1
                
                if relocation:
                    obj.relocations.append(relocation)
                    
            except Exception as e:
                raise SyntaxError(f"Line {line_num}: {e}")
        
        return obj
    
    def _compile_instruction(self, line: str, segment: str, offset: int) -> Tuple[int, Any, Any]:
        """
        Compiles a single instruction line.
        Returns (bytecode_word, extra_word_or_None, relocation_dict_or_None)
        """
        parts = line.split(maxsplit=1)
        mnemonic = parts[0].upper()
        
        if mnemonic not in self.InstructionSet:
            raise ValueError(f"Unknown instruction: {mnemonic}")
        
        operands = [op.strip() for op in parts[1].split(',')] if len(parts) > 1 else []
        bytecode_word = 0
        extra_word = None
        relocation = None
        
        # NOP, HALT, RTS
        if mnemonic in ['NOP', 'HALT', 'RTS']:
            bytecode_word = self.InstructionSet[mnemonic]
        
        # MOV
        elif mnemonic == 'MOV':
            destType, destVal = self.ParseOperand(operands[0])
            srcType, srcVal = self.ParseOperand(operands[1])
            opcode = self.InstructionSet[mnemonic]
            bytecode_word = opcode | GenerateSourceRegister(srcVal) | GenerateDestinationRegister(destVal)
        
        # ALU Operations
        elif mnemonic in ['ADD', 'SUB', 'MUL', 'DIV', 'SHL', 'AND', 'OR', 'XOR']:
            destType, destVal = self.ParseOperand(operands[0] if len(operands) > 0 else 'REA')
            srcType, srcVal = self.ParseOperand(operands[1] if len(operands) > 1 else 'REB')
            
            if destType != 'register' or srcType != 'register':
                raise SyntaxError(f"{mnemonic} requires register operands")
            
            opcode = self.InstructionSet[mnemonic]
            bytecode_word = opcode | GenerateSourceRegister(srcVal) | GenerateDestinationRegister(destVal)
        
        # LDI
        elif mnemonic == 'LDI':
            destType, destVal = self.ParseOperand(operands[0])
            srcType, srcVal = self.ParseOperand(operands[1])
            
            if srcType == 'immediate':
                opcode = self.InstructionSet['LDI'][0]
                bytecode_word = opcode | GenerateDestinationRegister(destVal)
                extra_word = srcVal
            elif srcType == 'direct_address':
                opcode = self.InstructionSet['LDI'][1]
                bytecode_word = opcode | GenerateDestinationRegister(destVal)
                extra_word = srcVal
            elif srcType == 'register':
                opcode = self.InstructionSet['LDI'][2]
                bytecode_word = opcode | GenerateSourceRegister(srcVal) | GenerateDestinationRegister(destVal)    
                    
        # STR
        elif mnemonic == 'STR':
            srcType, srcVal = self.ParseOperand(operands[1])
            destType, destVal = self.ParseOperand(operands[0])
            
            if destType == 'direct_address':
                opcode = self.InstructionSet['STR'][0]
                bytecode_word = opcode | GenerateSourceRegister(srcVal)
                extra_word = destVal
            elif destType == 'register':
                opcode = self.InstructionSet['STR'][1]
                bytecode_word = opcode | GenerateSourceRegister(srcVal) | GenerateDestinationRegister(destVal)
            else:
                raise SyntaxError(f"STR destination must be a direct address or register: STR <[addr]>, <reg> or STR <reg>, <reg>")
        
        # JP, JPZ, JPC, CALL
        elif mnemonic in ['JP', 'JPZ', 'JPC', 'CALL']:
            opType, opVal = self.ParseOperand(operands[0])
            
            if opType == 'symbol':
                # Create relocation entry
                opcode = self.InstructionSet[mnemonic][0]
                bytecode_word = opcode
                extra_word = 0  # Placeholder
                relocation = {
                    'segment': segment,
                    'offset': offset + 1,  # +1 because extra_word is at next position
                    'type': 'absolute',
                    'symbol': opVal
                }
            elif opType in ['immediate', 'direct_address']:
                opcode = self.InstructionSet[mnemonic][0]
                bytecode_word = opcode
                extra_word = opVal
            elif opType == 'register':
                opcode = self.InstructionSet[mnemonic][1]
                bytecode_word = opcode | GenerateSourceRegister(opVal)
        
        return bytecode_word, extra_word, relocation


def main(input_file, output_file):
    assembler = Assembler(INSTRUCTION_SET, Register, ExpansionPortRegister)
    
    try:
        with open(input_file, 'r') as f:
            assembly_code = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        obj = assembler.Compile(assembly_code, input_file)
    except Exception as e:
        print(f"Assembly failed: {e}")
        sys.exit(1)
    
    # Write object file
    with open(output_file + ".obj", 'w') as f:
        json.dump(obj.to_dict(), f, indent=2)
    
    print(f"Object file generated: {output_file}.obj")
    print(f"Segments: {list(obj.segments.keys())}")
    print(f"Labels: {len(obj.labels)}")
    print(f"Relocations: {len(obj.relocations)}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python assembler.py <input.asm> <output>")
        sys.exit(1)
    
    main(sys.argv[1], sys.argv[2])
    