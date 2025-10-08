import re
import sys
from Values.Registers import *

def GenerateSourceRegister(pRegister):
    return (pRegister & 0x1F) << 8

def GenerateDestinationRegister(pRegister):
    return (pRegister & 0x1F) << 13

INSTRUCITON_SET = {
    # System Operations
    'NOP': 0x00,
    'HALT': 0x01,
    
    # Data Movement
    'MOV': 0x02,
    'LDI': [0x03, 0x04],
    'STR': [0x05, 0x06],
    
    # ALU Operations
    'ADD': 0x07,
    'SUB': 0x08,
    'MUL': 0x09,
    'DIV': 0x0A,
    'SHL': 0x0B,
    'AND': 0x0C,
    'OR': 0x0D,
    'XOR': 0x0E,

    # Control Flow    
    'JP': [0x0F, 0x10],
}

class Assembler:
    def __init__(self, pInstructionSet, pRegisters, pPortRegisters):
        self.InstructionSet = pInstructionSet
        self.Registers = pRegisters
        self.PortRegisters = pPortRegisters
        self.Bytecode: list[int] = []
        self.CurrentAddress = 0
        self.Labels = {}
        self.RawLines = []

    def ParseRegister(self, pToken: str) -> int:
        """Looks up a register mnemonic and returns its 5-bit ID."""
        return getattr(self.Registers, pToken.upper())
        
    def ParsePortRegister(self, pToken: str) -> int:
        """Looks up a port mnemonic and returns its 5-bit ID."""
        return getattr(self.PortRegisters, pToken.upper())

    def ParseOperand(self, pOperand: str):
        """Determines the type and value of an operand."""
        pOperand = pOperand.strip()
        
        # 1. Immediate Value: #100 or #0xA0
        if pOperand.startswith('#'):
            try:
                value = int(pOperand[1:], 0)
                return 'immediate', value
            except ValueError:
                raise ValueError(f"Invalid immediate value: {pOperand}")
        
        # 2. Direct Address: [0x1000] (for LDI/STR Direct)
        elif pOperand.startswith('[') and pOperand.endswith(']'):
            addressStr = pOperand[1:-1].strip()
            try:
                address = int(addressStr, 0)
                return 'direct_address', address
            except ValueError:
                raise ValueError(f"Invalid direct address: {pOperand}")
        
        # 3. Register/Port: R0, EP1
        elif hasattr(self.Registers, pOperand.upper()):
            return 'register', self.ParseRegister(pOperand)
        elif hasattr(self.PortRegisters, pOperand.upper()):
            return 'register', self.ParsePortRegister(pOperand)
        
        # 4. Label/Symbol (Used in JP instructions)
        elif re.match(r'^[A-Z_][A-Z0-9_]*$', pOperand.upper()):
            return 'symbol', pOperand.upper()
        
        else:
            raise ValueError(f"Unrecognized operand format: {pOperand}")

    def ResolveLabels(self):
        """Pass 1: Scans code to find and record the address of every label."""
        self.Labels = {}
        address_counter = 0
        
        for line in self.RawLines:
            # 1. Strip comments and whitespace
            if ';' in line:
                line = line[:line.find(';')]
            line = line.strip()

            if not line:
                continue

            # 2. Check for Label Definition
            if line.endswith(':'):
                label_name = line[1:].strip().upper()
                if label_name in self.Labels:
                    raise SyntaxError(f"Duplicate label definition: {label_name}")
                self.Labels[label_name] = address_counter
                continue # Labels don't consume memory

            # 3. Estimate Instruction Size (Consume memory)
            parts = line.split(maxsplit=1)
            mnemonic = parts[0].upper()

            if mnemonic not in self.InstructionSet:
                continue 

            is_two_word = False
            
            # Check for two-word instructions (LDI/STR/JP direct)
            if mnemonic in ['LDI', 'STR', 'JP']:
                operands_str = parts[1] if len(parts) > 1 else ''
                operands = [op.strip() for op in operands_str.split(',')]
                
                if mnemonic == 'JP' and not hasattr(self.Registers, operands[0].upper()) and not hasattr(self.PortRegisters, operands[0].upper()):
                    is_two_word = True
                
                elif mnemonic in ['LDI', 'STR']:
                    second_operand = operands[1] if len(operands) > 1 else ''
                    if second_operand.startswith('#') or second_operand.startswith('['):
                        is_two_word = True

            address_counter += 2 if is_two_word else 1
     
    def CompileInstruction(self, pLine: str):
        """Pass 2: Processes a single line of assembly and adds bytecode."""
        
        # 1. Strip comments and whitespace
        if ';' in pLine:
            pLine = pLine[:pLine.find(';')]
        pLine = pLine.strip()

        if not pLine or pLine.startswith(':'):
            return

        parts = pLine.split(maxsplit=1)
        mnemonic = parts[0].upper()
        
        operands = []
        if len(parts) > 1:
            # Note: This split/strip handles internal comments as well if they were not already removed (e.g., MOV R1, R2 ; comment)
            operands = [op.strip() for op in parts[1].split(',')]

        bytecodeWord = 0
        extraWord = None

        if mnemonic not in self.InstructionSet:
            raise ValueError(f"Unknown instruction mnemonic: {mnemonic}")
        
        # --- 0. NOP, HALT (Zero Operand) ---- #
        if mnemonic in ['NOP', 'HALT']:
            if len(operands) > 1: # Check if there are no operands
                raise SyntaxError(f"{mnemonic} takes no operands.")
            bytecodeWord = self.InstructionSet[mnemonic]

        elif mnemonic == 'MOV':
            if len(operands) != 2:
                raise SyntaxError(f"{mnemonic} requires two or non operands: (Dest, Src).")
            
            destType, destVal = self.ParseOperand(operands[0])
            srcType, srcVal = self.ParseOperand(operands[1])

            if destType != 'register' or srcType != 'register':
                raise SyntaxError(f"{mnemonic} only supports Register/Port operands (Dest, Src).")

            opcode = self.InstructionSet[mnemonic]
            bytecodeWord = opcode
            bytecodeWord |= GenerateSourceRegister(srcVal)
            bytecodeWord |= GenerateDestinationRegister(destVal)
            
        
        # TODO: make ALU operations more flexible (e.g., support immediate values: ADD R1, #5 or SUB R1, [0x100] or MUL #10, #20)
        elif mnemonic in ['ADD', 'SUB', 'MUL', 'DIV', 'SHL', 'AND', 'OR', 'XOR']:
            if len(operands) == 1 or len(operands) > 2:
                raise SyntaxError(f"{mnemonic} requires two or non operands: Reg1, Reg2.")
            
            destType, destVal = self.ParseOperand(operands[0] if len(operands) else 'REA') # Using A/ B register as default for operation
            srcType, srcVal = self.ParseOperand(operands[1] if len(operands) else 'REB')

            if destType != 'register' or srcType != 'register':
                raise SyntaxError(f"{mnemonic} only supports Register/Port operands (Dest, Src).")

            opcode = self.InstructionSet[mnemonic]
            bytecodeWord = opcode
            bytecodeWord |= GenerateSourceRegister(srcVal)
            bytecodeWord |= GenerateDestinationRegister(destVal)
        
        # --- 2. LDI (Load) Overloading ---
        elif mnemonic == 'LDI':
            if len(operands) != 2:
                raise SyntaxError(f"LDI requires two operands: Dest, Src.")
            
            destType, destVal = self.ParseOperand(operands[0])
            srcType, srcVal = self.ParseOperand(operands[1])

            if destType != 'register':
                 raise SyntaxError(f"LDI destination must be a Register/Port.")
            
            if srcType == 'immediate':
                opcode = self.InstructionSet['LDI'][0]
                bytecodeWord = opcode | GenerateDestinationRegister(destVal)
                extraWord = srcVal
            
            elif srcType == 'direct_address':
                opcode = self.InstructionSet['LDI'][1]
                bytecodeWord = opcode | GenerateDestinationRegister(destVal)
                extraWord = srcVal

            else:
                 raise SyntaxError(f"LDI source must be Immediate (#) or Direct Address ([]).")

        # --- 3. STR (Store) Overloading ---
        elif mnemonic == 'STR':
            if len(operands) != 2:
                raise SyntaxError(f"STR requires two operands: Src, Dest_Address.")
            
            srcType, srcVal = self.ParseOperand(operands[0])
            destType, destVal = self.ParseOperand(operands[1])

            if srcType != 'register':
                 raise SyntaxError(f"STR source must be a Register/Port.")
            
            if destType == 'direct_address':
                opcode = self.InstructionSet['STR'][0]
                bytecodeWord = opcode | GenerateSourceRegister(srcVal)
                extraWord = destVal

            elif destType == 'register':
                opcode = self.InstructionSet['STR'][1]
                bytecodeWord = opcode 
                bytecodeWord |= GenerateSourceRegister(srcVal)
                bytecodeWord |= GenerateDestinationRegister(destVal)

            else:
                 raise SyntaxError(f"STR destination must be Direct Address ([]) or Address Register (R/EP).")
            
        # --- 4. JP (Jump) Overloading ---
        elif mnemonic == 'JP':
            if len(operands) != 1:
                raise SyntaxError(f"JP requires one operand: Address, Label, or Register.")

            opType, opVal = self.ParseOperand(operands[0])

            # JP Label or JP 0xAddress (Jump Absolute) -> Opcode 0x0F
            if opType in ['immediate', 'direct_address', 'symbol']:
                opcode = self.InstructionSet['JP'][0] # 0x0F

                if opType == 'symbol':
                    if opVal not in self.Labels:
                        raise SyntaxError(f"Undefined label: {opVal}")
                    jump_address = self.Labels[opVal]
                else:
                    jump_address = opVal

                bytecodeWord = opcode 
                extraWord = jump_address

            # JP REA (Jump Indirect) -> Opcode 0x10
            elif opType == 'register':
                opcode = self.InstructionSet['JP'][1] # 0x10
                bytecodeWord = opcode | GenerateSourceRegister(opVal) # Use Source field for jump register
                # Note: The Destination register might need to be PC for some architectures, 
                # but we'll assume the Opcode 0x10 microcode handles the jump implicitly.
                # If your hardware requires the destination field to hold a register (e.g., R0), adjust here.

            else:
                raise SyntaxError(f"JP operand must be an Address, Label, or Register.")

        # --- END OF INSTRUCTION LOGIC ---

        # Add instruction word
        self.Bytecode.append(bytecodeWord)
        self.CurrentAddress += 1

        # Add extra word for 2-word instructions
        if extraWord is not None:
            self.Bytecode.append(extraWord)
            self.CurrentAddress += 1

    def Compile(self, AssemblyCode: str) -> list[int]:
        """Compiles the full assembly code string using two passes."""
        self.RawLines = AssemblyCode.split('\n')
        
        # Pass 1: Resolve Labels
        self.ResolveLabels() 

        # Pass 2: Compile Instructions
        self.Bytecode = []
        self.CurrentAddress = 0
        
        for line in self.RawLines:
            try:
                self.CompileInstruction(line)
            except Exception as e:
                print(f"Error compiling line: '{line.strip()}' -> {e}")
                raise 
        
        return self.Bytecode               

assembler = Assembler(INSTRUCITON_SET, Register, ExpasionPortRegister)

inputFile = sys.argv[1]
outputFile = sys.argv[2]

if (inputFile is None) or (outputFile is None):
    print("Usage: python AssemblyCompiler.py <input.asm> <output>")
    sys.exit(1)

with open(inputFile) as file:
    byteCode = assembler.Compile(file.read())

with open(outputFile+".o", mode="w") as file:
    fileContent = "v2.0 raw\n"
    for i in range(0, len(byteCode), 4):
        row = byteCode[i:i+4]
        fileContent += ' '.join(f"{word:06X}" for word in row) + "\n"
        
    file.write(fileContent)

print("File generated:", outputFile)
print("Content:")
print(fileContent)
