import re
import sys
import os
import json
from Values.Registers import *
from typing import Dict, List, Tuple, Any


def GenerateSourceRegister(pRegister: int) -> int:
    return (pRegister & 0x1F) << 8

def GenerateDestinationRegister(pRegister: int) -> int:
    return (pRegister & 0x1F) << 12

def GenerateALUAInput(pRegister: int) -> int:
    return (pRegister & 0xF) << 16

def GenerateALUBInput(pRegister: int) -> int:
    print(pRegister)
    return (pRegister & 0xF) << 20



INSTRUCTION_SET = {
    'NOP': 0x00, 
    'HALT': 0x01,
    'MOV': 0x02, 
    'LDI': [0x03, 0x04, 0x05], 
    'STR': [0x06, 0x07],
    'ADD': 0x08,
    'SUB': 0x09,
    'MUL': 0x0A,
    'DIV': 0x0B, 
    'SHL': 0x0C,
    'SHR': 0x0D,
    'NAND': 0x0E,
    'AND': 0x0F,
    'OR': 0x10,
    'XOR': 0x11,
    'NOR': 0x12,
    'NOT': 0x13,
    'JP': [0x14, 0x15],
    'JPZ': [0x16, 0x17],
    'JPC': [0x18, 0x19],
    'CALL': [0x1A, 0x1B],
    'RTS': 0x1C,
    'PUSH': [0x1D, 0x1E],
    'POP': 0x1F,
    'SET_SP': 0x20,
    'GET_SP': 0x21,
    'GET_PC': 0x22,
    'SET_IVR': 0x23,

    'RTI': 0xFE,
    'INT': 0xFF
}


class RelocatableObject:
    """Represents a compiled object file with relocation info."""
    def __init__(self, filename: str):
        self.filename = filename
        self.segments: Dict[str, List[int]] = {}  
        self.labels: Dict[str, Tuple[str, int]] = {}  
        self.relocations: List[Dict[str, Any]] = []  
        self.imports: List[str] = [] 
        
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


class Assembler:
    def __init__(self, pInstructionSet, pRegisters, pSourceDir='.'):
        self.InstructionSet = pInstructionSet
        self.Registers = pRegisters
        self.SourceDir = pSourceDir
        
    def ParseRegister(self, pToken: str) -> int:
        return getattr(self.Registers, pToken.upper())
        
    def IsRegister(self, pToken: str) -> bool:
        return hasattr(self.Registers, pToken.upper())

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
        elif re.match(r'^[A-Za-z_][A-Za-z0-9_.]*$', pOperand):
            return 'symbol', pOperand  # Preserve original case
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
        segment_offset = 0  
        import_namespaces = {} 
        
        for line in lines:
            if ';' in line:
                line = line[:line.find(';')]
            line = line.strip()
            if not line:
                continue
            
            if line.upper().startswith('!IMPORT'):
                match = re.match(r'!IMPORT\s+(["\']?)([^"\']+)\1(?:\s+AS\s+(\S+))?', line, re.IGNORECASE)
                if match:
                    import_file = match.group(2)  # Get the filename without quotes
                    namespace = match.group(3).upper() if match.group(3) else os.path.basename(import_file).replace('.asm', '').upper()
                    import_namespaces[import_file] = namespace
        
        for line_num, line in enumerate(lines, 1):
            # Cleanup
            if ';' in line:
                line = line[:line.find(';')]
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('.'):
                current_segment = line[1:].strip()  # Preserve original case
                if current_segment not in obj.segments:
                    obj.segments[current_segment] = []
                segment_offset = len(obj.segments[current_segment])
                continue
            
            # Check for import directive
            if line.upper().startswith('!IMPORT'):
                match = re.match(r'!IMPORT\s+(["\']?)([^"\']+)\1(?:\s+AS\s+(\S+))?', line, re.IGNORECASE)
                if match:
                    import_file = match.group(2)  # Get the filename without quotes
                    obj.imports.append(import_file)
                continue
            
            # Check for label definition
            if line.endswith(':'):
                if current_segment is None:
                    raise SyntaxError(f"Line {line_num}: Label '{line[:-1]}' defined outside any segment")
                label_name = line[:-1].strip()  # Preserve original case
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
        if mnemonic in ['NOP', 'HALT', 'RTS', 'RTI', 'INT']:
            bytecode_word = self.InstructionSet[mnemonic]
        
        # MOV
        elif mnemonic == 'MOV':
            destType, destVal = self.ParseOperand(operands[0])
            srcType, srcVal = self.ParseOperand(operands[1])
            opcode = self.InstructionSet[mnemonic]
            bytecode_word = opcode | GenerateSourceRegister(srcVal) | GenerateDestinationRegister(destVal)
        
        # ALU Operations
        elif mnemonic in ['ADD', 'SUB', 'MUL', 'DIV', 'SHL', 'SHR', 'NAND', 'AND', 'OR', 'XOR', 'NOR']:
            opcode = self.InstructionSet[mnemonic]
            
            if len(operands) == 2:
                # 2-operand format: ADD REA, REX (add REX to REA, store in REA)
                destType, destVal = self.ParseOperand(operands[0])
                srcType, srcVal = self.ParseOperand(operands[1])
                
                if destType != 'register' or srcType != 'register':
                    raise SyntaxError(f"{mnemonic} requires register operands")
                
                # A-input = dest register, B-input = src register, destination = dest register
                bytecode_word = (opcode | 
                               GenerateALUAInput(destVal) | 
                               GenerateALUBInput(srcVal) | 
                               GenerateDestinationRegister(destVal))
                
            elif len(operands) == 3:
                # 3-operand format: ADD REX, REY, REZ (add REY to REX, store in REZ)
                aInputType, aInputVal = self.ParseOperand(operands[0])
                bInputType, bInputVal = self.ParseOperand(operands[1])
                destType, destVal = self.ParseOperand(operands[2])
                
                if aInputType != 'register' or bInputType != 'register' or destType != 'register':
                    raise SyntaxError(f"{mnemonic} requires register operands")
                
                # A-input = first operand, B-input = second operand, destination = third operand
                bytecode_word = (opcode | 
                               GenerateALUAInput(aInputVal) | 
                               GenerateALUBInput(bInputVal) | 
                               GenerateDestinationRegister(destVal))
            else:
                raise SyntaxError(f"{mnemonic} requires either 2 or 3 operands, got {len(operands)}")
        
        # NOT operation (unary)
        elif mnemonic == 'NOT':
            opcode = self.InstructionSet[mnemonic]
            
            if len(operands) == 1:
                # 1-operand format: NOT REA (NOT REA, store in REA)
                destType, destVal = self.ParseOperand(operands[0])
                
                if destType != 'register':
                    raise SyntaxError(f"{mnemonic} requires register operand")
                
                # A-input = dest register, B-input = 0 (unused), destination = dest register
                bytecode_word = (opcode | 
                               GenerateALUAInput(destVal) | 
                               GenerateALUBInput(0) | 
                               GenerateDestinationRegister(destVal))
                
            elif len(operands) == 2:
                # 2-operand format: NOT REA, REB (NOT REA, store in REB)
                srcType, srcVal = self.ParseOperand(operands[0])
                destType, destVal = self.ParseOperand(operands[1])
                
                if srcType != 'register' or destType != 'register':
                    raise SyntaxError(f"{mnemonic} requires register operands")
                
                # A-input = src register, B-input = 0 (unused), destination = dest register
                bytecode_word = (opcode | 
                               GenerateALUAInput(srcVal) | 
                               GenerateALUBInput(0) | 
                               GenerateDestinationRegister(destVal))
            else:
                raise SyntaxError(f"{mnemonic} requires either 1 or 2 operands, got {len(operands)}")
        
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
            elif srcType == 'symbol':
                # Create relocation for symbol
                opcode = self.InstructionSet['LDI'][0]  # Use immediate variant
                bytecode_word = opcode | GenerateDestinationRegister(destVal)
                extra_word = 0  # Placeholder
                relocation = {
                    'segment': segment,
                    'offset': offset + 1,  # +1 because extra_word is at next position
                    'type': 'absolute',
                    'symbol': srcVal
                }
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
            elif destType == 'symbol':
                # Create relocation for symbol
                opcode = self.InstructionSet['STR'][0]  # Use direct address variant
                bytecode_word = opcode | GenerateSourceRegister(srcVal)
                extra_word = 0  # Placeholder
                relocation = {
                    'segment': segment,
                    'offset': offset + 1,  # +1 because extra_word is at next position
                    'type': 'absolute',
                    'symbol': destVal
                }
            elif destType == 'register':
                opcode = self.InstructionSet['STR'][1]
                bytecode_word = opcode | GenerateSourceRegister(srcVal) | GenerateDestinationRegister(destVal)
            else:
                raise SyntaxError(f"STR destination must be a direct address, symbol, or register: STR <[addr]>, <reg> or STR <symbol>, <reg> or STR <reg>, <reg>")
        
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
        
        # PUSH
        elif mnemonic == 'PUSH':
            srcType, srcVal = self.ParseOperand(operands[0])
            
            if srcType == 'register':
                opcode = self.InstructionSet['PUSH'][0]
                bytecode_word = opcode | GenerateSourceRegister(srcVal)
            elif srcType == 'immediate':
                opcode = self.InstructionSet['PUSH'][1]
                bytecode_word = opcode
                extra_word = srcVal
            elif srcType == 'symbol':
                # Create relocation for symbol
                opcode = self.InstructionSet['PUSH'][1]  # Use immediate variant
                bytecode_word = opcode
                extra_word = 0  # Placeholder
                relocation = {
                    'segment': segment,
                    'offset': offset + 1,  # +1 because extra_word is at next position
                    'type': 'absolute',
                    'symbol': srcVal
                }
            else:
                raise SyntaxError(f"PUSH operand must be a register, immediate value, or symbol")
        
        # POP
        elif mnemonic == 'POP':
            destType, destVal = self.ParseOperand(operands[0])
            
            if destType == 'register':
                opcode = self.InstructionSet['POP']
                bytecode_word = opcode | GenerateDestinationRegister(destVal)
            else:
                raise SyntaxError(f"POP operand must be a register")
        
        # SET_SP
        elif mnemonic == 'SET_SP':
            srcType, srcVal = self.ParseOperand(operands[0])
            
            if srcType == 'immediate':
                opcode = self.InstructionSet['SET_SP']
                bytecode_word = opcode
                extra_word = srcVal
            elif srcType == 'symbol':
                # Create relocation for symbol
                opcode = self.InstructionSet['SET_SP']
                bytecode_word = opcode
                extra_word = 0  # Placeholder
                relocation = {
                    'segment': segment,
                    'offset': offset + 1,  # +1 because extra_word is at next position
                    'type': 'absolute',
                    'symbol': srcVal
                }
            else:
                raise SyntaxError(f"SET_SP operand must be an immediate value or symbol")
        
        # GET_SP
        elif mnemonic == 'GET_SP':
            destType, destVal = self.ParseOperand(operands[0])
            
            if destType == 'register':
                opcode = self.InstructionSet['GET_SP']
                bytecode_word = opcode | GenerateDestinationRegister(destVal)
            else:
                raise SyntaxError(f"GET_SP operand must be a register")
        
        # GET_PC
        elif mnemonic == 'GET_PC':
            destType, destVal = self.ParseOperand(operands[0])
            
            if destType == 'register':
                opcode = self.InstructionSet['GET_PC']
                bytecode_word = opcode | GenerateDestinationRegister(destVal)
            else:
                raise SyntaxError(f"GET_PC operand must be a register")
            
        # SET_IVR
        elif mnemonic == 'SET_IVR':
            srcType, srcVal = self.ParseOperand(operands[0])
            
            if srcType == 'immediate':
                opcode = self.InstructionSet['SET_IVR']
                bytecode_word = opcode
                extra_word = srcVal
            elif srcType == 'symbol':
                # Create relocation for symbol
                opcode = self.InstructionSet['SET_IVR']
                bytecode_word = opcode
                extra_word = 0  # Placeholder
                relocation = {
                    'segment': segment,
                    'offset': offset + 1,  # +1 because extra_word is at next position
                    'type': 'absolute',
                    'symbol': srcVal
                }
            else:
                raise SyntaxError(f"SET_IVR operand must be an immediate value or symbol")
        
        return bytecode_word, extra_word, relocation


def main(input_file, output_file):
    assembler = Assembler(INSTRUCTION_SET, Register)
    
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
    
    # Determine output directory structure based on input file path
    input_path = os.path.normpath(input_file)
    input_parts = input_path.split(os.sep)
    
    # Check if we should auto-determine the output path
    if output_file is None and 'src' in input_parts:
        src_index = input_parts.index('src')
        # Get the path before 'src'
        base_path = os.sep.join(input_parts[:src_index])
        # Get the relative path after 'src'
        relative_path = os.sep.join(input_parts[src_index + 1:])
        # Remove the .asm extension
        relative_path_no_ext = os.path.splitext(relative_path)[0]
        
        # Create the bin directory structure
        bin_dir = os.path.join(base_path, 'bin', os.path.dirname(relative_path_no_ext))
        if bin_dir and not os.path.exists(bin_dir):
            os.makedirs(bin_dir, exist_ok=True)
        
        # Determine the final output file path
        final_output = os.path.join(base_path, 'bin', relative_path_no_ext)
    elif output_file is not None:
        # Use the provided output file
        final_output = output_file
        output_dir = os.path.dirname(final_output + ".obj")
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    else:
        # Fallback: use input filename without extension in current directory
        final_output = os.path.splitext(os.path.basename(input_file))[0]
    
    # Write object file
    with open(final_output + ".obj", 'w') as f:
        json.dump(obj.to_dict(), f, indent=2)
    
    print(f"Object file generated: {final_output}.obj")
    print(f"Segments: {list(obj.segments.keys())}")
    print(f"Labels: {len(obj.labels)}")
    print(f"Relocations: {len(obj.relocations)}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python Compiler.py <input.asm> [output_base_name]")
        print("If output_base_name is not provided, directory structure will be auto-determined from input path")
        print("Example: python Compiler.py os/src/drivers/JoystickDriver.asm")
        print("         -> outputs to os/bin/drivers/JoystickDriver.obj")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    main(input_file, output_file)
    