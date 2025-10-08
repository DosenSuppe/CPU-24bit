import re
import sys
from Values.Registers import *

def GenerateSourceRegister(pRegister):
    return (pRegister & 0x1F) << 8

def GenerateDestinationRegister(pRegister):
    return (pRegister & 0x1F) << 13

INSTRUCITON_SET = {
    'NOP': 0x00,
    'HALT': 0x01,
    'MOV': 0x02,
    'LDI': [0x03, 0x04],
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
            line = line.strip()
            if not line or line.startswith(';'):
                continue

            # 1. Check for Label Definition
            if line.startswith(':'):
                label_name = line[1:].strip().upper()
                if label_name in self.Labels:
                    raise SyntaxError(f"Duplicate label definition: {label_name}")
                self.Labels[label_name] = address_counter
                continue # Labels don't consume memory

            # 2. Estimate Instruction Size (Consume memory)
            parts = line.split(maxsplit=1)
            mnemonic = parts[0].upper()

            # Skip instruction if mnemonic is not in the set (for safety, though it'll fail later)
            if mnemonic not in self.InstructionSet:
                continue 

            is_two_word = False
            
            # Check for two-word instructions (LDI/STR/JP direct)
            if mnemonic in ['LDI', 'STR', 'JP']:
                operands_str = parts[1] if len(parts) > 1 else ''
                operands = [op.strip() for op in operands_str.split(',')]
                
                # Heuristics to check for 2-word instructions
                if mnemonic == 'JP' and not hasattr(self.Registers, operands[0].upper()) and not hasattr(self.PortRegisters, operands[0].upper()):
                    # JP followed by immediate/label is 2 words (JP 0xAddr or JP Label)
                    is_two_word = True
                
                elif mnemonic in ['LDI', 'STR']:
                    # LDI R, #Value OR LDI R, [Addr] OR STR R, [Addr]
                    # We check for a non-register second operand (Immediate or Direct Address)
                    second_operand = operands[1] if len(operands) > 1 else ''
                    if second_operand.startswith('#') or second_operand.startswith('['):
                        is_two_word = True

            address_counter += 2 if is_two_word else 1
      
    def CompileInstruction(self, pLine: str):
        """Pass 2: Processes a single line of assembly and adds bytecode."""
        pLine = pLine.strip()
        if not pLine or pLine.startswith(';') or pLine.startswith(':'):
            return

        parts = pLine.split(maxsplit=1)
        mnemonic = parts[0].upper()
        
        operands = []
        if len(parts) > 1:
            operands = [op.strip() for op in parts[1].split(',')]

        bytecodeWord = 0
        extraWord = None

        if mnemonic not in self.InstructionSet:
            raise ValueError(f"Unknown instruction mnemonic: {mnemonic}")
        
        # --- 0. NOP, HALT (Zero Operand) ---- #
        if mnemonic in ['NOP', 'HALT']:
            if len(operands) != 0:
                raise SyntaxError(f"{mnemonic} takes no operands.")
            bytecodeWord = self.InstructionSet[mnemonic]

        # --- 1. MOV, ALU (Two Operand: DEST, SRC) ---
        elif mnemonic in ['MOV', 'ADD', 'SUB', 'MUL', 'DIV', 'SHL', 'AND', 'OR', 'XOR']:
            if len(operands) != 2:
                raise SyntaxError(f"{mnemonic} requires two operands: Dest, Src.")
            
            destType, destVal = self.ParseOperand(operands[0])
            srcType, srcVal = self.ParseOperand(operands[1])

            if destType != 'register' or srcType != 'register':
                raise SyntaxError(f"{mnemonic} only supports Register/Port operands (Dest, Src).")

            opcode = self.InstructionSet[mnemonic]
            bytecodeWord = opcode
            bytecodeWord |= GenerateSourceRegister(srcVal) # Src is the second operand
            bytecodeWord |= GenerateDestinationRegister(destVal) # Dest is the first operand
        
        # --- 2. LDI (Load) Overloading: LDI R_dest, #Value or LDI R_dest, [Address] ---
        elif mnemonic == 'LDI':
            if len(operands) != 2:
                raise SyntaxError(f"LDI requires two operands: Dest, Src.")
            
            destType, destVal = self.ParseOperand(operands[0])
            srcType, srcVal = self.ParseOperand(operands[1])

            if destType != 'register':
                 raise SyntaxError(f"LDI destination must be a Register/Port.")
            
            # LDI R_dest, #Value (Load Immediate)
            if srcType == 'immediate':
                opcode = self.InstructionSet['LDI'][0]
                bytecodeWord = opcode | GenerateDestinationRegister(destVal)
                extraWord = srcVal # The 24-bit immediate value
            
            # LDI R_dest, [Address] (Load Direct)
            elif srcType == 'direct_address':
                opcode = self.InstructionSet['LDI'][1]
                bytecodeWord = opcode | GenerateDestinationRegister(destVal)
                extraWord = srcVal # The 24-bit address

            else:
                 raise SyntaxError(f"LDI source must be Immediate (#) or Direct Address ([]).")

        # --- 3. STR (Store) Overloading: STR R_src, [Address] or STR R_src, R_addr ---
        elif mnemonic == 'STR':
            if len(operands) != 2:
                raise SyntaxError(f"STR requires two operands: Src, Dest_Address.")
            
            srcType, srcVal = self.ParseOperand(operands[0])
            destType, destVal = self.ParseOperand(operands[1])

            if srcType != 'register':
                 raise SyntaxError(f"STR source must be a Register/Port.")
            
            # STR R_src, [Address] (Store Direct) -> Opcode 0x05
            if destType == 'direct_address':
                opcode = self.InstructionSet['STR'][0] # 0x05
                bytecodeWord = opcode | GenerateSourceRegister(srcVal)
                extraWord = destVal

            # STR R_src, R_addr (Store Indirect) -> Opcode 0x06
            elif destType == 'register':
                opcode = self.InstructionSet['STR'][1] # 0x06
                bytecodeWord = opcode 
                bytecodeWord |= GenerateSourceRegister(srcVal) # R_src is the data source
                bytecodeWord |= GenerateDestinationRegister(destVal) # R_addr is the address register

            else:
                 raise SyntaxError(f"STR destination must be Direct Address ([]) or Address Register (R/EP).")
             
        elif mnemonic == 'JP':
            if len(operands) != 1:
                raise SyntaxError(f"JP requires one operand: Address, Label, or Register.")

            opType, opVal = self.ParseOperand(operands[0])

            # JP Label or JP 0xAddress (Jump Absolute) -> Opcode 0x0F
            if opType in ['immediate', 'direct_address', 'symbol']:
                opcode = self.InstructionSet['JP'][0] # 0x0F

                if opType == 'symbol':
                    # Resolve label address from Pass 1
                    if opVal not in self.Labels:
                        raise SyntaxError(f"Undefined label: {opVal}")
                    jump_address = self.Labels[opVal]
                else:
                    jump_address = opVal

                bytecodeWord = opcode 
                extraWord = jump_address # The 24-bit jump address

            # JP REA (Jump Indirect) -> Opcode 0x10
            elif opType == 'register':
                opcode = self.InstructionSet['JP'][1] # 0x10
                bytecodeWord = opcode | GenerateSourceRegister(opVal) # Use Source field for jump register
                bytecodeWord |= GenerateDestinationRegister(Register.PC)

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
                 # Raise the exception with the full line for better debugging
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
