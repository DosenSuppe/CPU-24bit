"""Instruction compilation handlers."""

from typing import Optional, Dict, Any
from CompilerComponents.InstructionSet import (
    INSTRUCTION_SET,
    GenerateSourceRegister,
    GenerateDestinationRegister,
    GenerateALUAInput,
    GenerateALUBInput
)
from CompilerComponents.OperandParser import OperandType
from CompilerComponents.Exceptions import InstructionError


class InstructionResult:
    """
    Result of compiling an instruction.
    
    Attributes:
        bytecode: The primary bytecode word
        extra_word: Optional second word for immediate values or addresses
        relocation: Optional relocation information for symbols
    """
    
    def __init__(self, pBytecode: int, pExtraWord: Optional[int] = None, 
                 pRelocation: Optional[Dict[str, Any]] = None):
        self.bytecode = pBytecode
        self.extraWord = pExtraWord
        self.relocation = pRelocation


class SimpleInstructionCompiler:
    """Compiler for simple instructions without operands."""
    
    @staticmethod
    def Compile(pMnemonic: str) -> InstructionResult:
        """
        Compile simple instructions (NOP, HALT, RTS, RTI, INT).
        
        Args:
            mnemonic: Instruction mnemonic
            
        Returns:
            InstructionResult with opcode
        """
        opcode = INSTRUCTION_SET[pMnemonic]
        return InstructionResult(opcode)


class MovInstructionCompiler:
    """Compiler for MOV instruction."""
    
    @staticmethod
    def Compile(pOperands: list) -> InstructionResult:
        """
        Compile MOV instruction: MOV dest, src
        
        Args:
            operands: List of parsed operands [(type, value), ...]
            
        Returns:
            InstructionResult with encoded instruction
        """
        if len(pOperands) != 2:
            raise InstructionError(f"MOV requires 2 operands, got {len(pOperands)}")
        
        destType, destVal = pOperands[0]
        srcType, srcVal = pOperands[1]
        
        if destType != OperandType.REGISTER or srcType != OperandType.REGISTER:
            raise InstructionError("MOV requires register operands")
        
        opcode = INSTRUCTION_SET['MOV']
        bytecode = (opcode | 
                   GenerateSourceRegister(srcVal) | 
                   GenerateDestinationRegister(destVal))
        
        return InstructionResult(bytecode)


class ALUInstructionCompiler:
    """Compiler for ALU operations."""
    
    @staticmethod
    def CompileBinary(pMnemonic: str, pOperands: list) -> InstructionResult:
        """
        Compile binary ALU operations (ADD, SUB, MUL, DIV, etc.).

        Supports four formats:
        - 2-operand register:   ADD REA, REB         (REA = REA op REB)
        - 2-operand immediate:  ADD REA, #5          (REA = REA op 5)
        - 3-operand register:   ADD REX, REY, REZ    (REZ = REX op REY)
        - 3-operand immediate:  ADD REX, #5, REZ     (REZ = REX op 5)

        The immediate form uses a distinct opcode (INSTRUCTION_SET[mnemonic][1])
        and emits a second word containing the 24-bit immediate.
        """
        opcodes = INSTRUCTION_SET[pMnemonic]

        if len(pOperands) == 2:
            return ALUInstructionCompiler._CompileTwoOperand(pMnemonic, opcodes, pOperands)
        elif len(pOperands) == 3:
            return ALUInstructionCompiler._CompileThreeOperand(pMnemonic, opcodes, pOperands)
        else:
            raise InstructionError(
                f"{pMnemonic} requires 2 or 3 operands, got {len(pOperands)}"
            )

    @staticmethod
    def _CompileTwoOperand(mnemonic: str, opcodes: list, operands: list) -> InstructionResult:
        """Compile 2-operand ALU instruction (register or immediate B-input)."""
        destType, destVal = operands[0]
        srcType, srcVal = operands[1]

        if destType != OperandType.REGISTER:
            raise InstructionError(f"{mnemonic} destination must be a register")

        # Register form: dest = dest op src
        if srcType == OperandType.REGISTER:
            opcode = opcodes[0]
            bytecode = (opcode |
                       GenerateALUAInput(destVal) |
                       GenerateALUBInput(srcVal) |
                       GenerateDestinationRegister(destVal))
            return InstructionResult(bytecode)

        # Immediate form: dest = dest op #imm (immediate is the B input,
        # carried in the extra word; B field in the opcode is unused).
        elif srcType == OperandType.IMMEDIATE:
            opcode = opcodes[1]
            bytecode = (opcode |
                       GenerateALUAInput(destVal) |
                       GenerateDestinationRegister(destVal))
            return InstructionResult(bytecode, pExtraWord=srcVal)

        else:
            raise InstructionError(
                f"{mnemonic} second operand must be a register or immediate"
            )

    @staticmethod
    def _CompileThreeOperand(mnemonic: str, opcodes: list, operands: list) -> InstructionResult:
        """Compile 3-operand ALU instruction (register or immediate B-input)."""
        aType, aVal = operands[0]
        bType, bVal = operands[1]
        destType, destVal = operands[2]

        if aType != OperandType.REGISTER:
            raise InstructionError(f"{mnemonic} first operand must be a register")
        if destType != OperandType.REGISTER:
            raise InstructionError(f"{mnemonic} destination must be a register")

        # Register form: dest = a op b
        if bType == OperandType.REGISTER:
            opcode = opcodes[0]
            bytecode = (opcode |
                       GenerateALUAInput(aVal) |
                       GenerateALUBInput(bVal) |
                       GenerateDestinationRegister(destVal))
            return InstructionResult(bytecode)

        # Immediate form: dest = a op #imm
        elif bType == OperandType.IMMEDIATE:
            opcode = opcodes[1]
            bytecode = (opcode |
                       GenerateALUAInput(aVal) |
                       GenerateDestinationRegister(destVal))
            return InstructionResult(bytecode, pExtraWord=bVal)

        else:
            raise InstructionError(
                f"{mnemonic} second operand must be a register or immediate"
            )
    
    @staticmethod
    def CompileUnary(pMnemonic: str, pOperands: list) -> InstructionResult:
        """
        Compile unary ALU operations (NOT).
        
        Supports two formats:
        - 1-operand: NOT REA  (REA = NOT REA)
        - 2-operand: NOT REA, REB  (REB = NOT REA)
        
        Args:
            mnemonic: Instruction mnemonic
            operands: List of parsed operands
            
        Returns:
            InstructionResult with encoded instruction
        """
        opcode = INSTRUCTION_SET[pMnemonic]
        
        if len(pOperands) == 1:
            destType, destVal = pOperands[0]
            
            if destType != OperandType.REGISTER:
                raise InstructionError(f"{pMnemonic} requires register operand")
            
            bytecode = (opcode | 
                       GenerateALUAInput(destVal) | 
                       GenerateALUBInput(0) | 
                       GenerateDestinationRegister(destVal))
            
        elif len(pOperands) == 2:
            srcType, srcVal = pOperands[0]
            destType, destVal = pOperands[1]
            
            if srcType != OperandType.REGISTER or destType != OperandType.REGISTER:
                raise InstructionError(f"{pMnemonic} requires register operands")
            
            bytecode = (opcode | 
                       GenerateALUAInput(srcVal) | 
                       GenerateALUBInput(0) | 
                       GenerateDestinationRegister(destVal))
        else:
            raise InstructionError(
                f"{pMnemonic} requires 1 or 2 operands, got {len(pOperands)}"
            )
        
        return InstructionResult(bytecode)


class CMPInstructionCompiler:
    """Compiler for CMP (Compare) instruction - sets flags without modifying registers."""
    
    @staticmethod
    def Compile(pOperands: list) -> InstructionResult:
        """Compile CMP instruction: CMP REA, REB"""
        if len(pOperands) != 2:
            raise InstructionError(f"CMP requires 2 operands, got {len(pOperands)}")
        
        aType, aVal = pOperands[0]
        bType, bVal = pOperands[1]
        
        if aType != OperandType.REGISTER or bType != OperandType.REGISTER:
            raise InstructionError("CMP requires register operands")
        
        opcode = INSTRUCTION_SET['CMP']
        bytecode = (opcode |
                   GenerateALUAInput(aVal) |
                   GenerateALUBInput(bVal))
        
        return InstructionResult(bytecode)

class LDR_LOCInstructionCompiler:
    """Compiler for LDR_LOC: load a register from a local frame slot at [FP - imm]."""

    @staticmethod
    def Compile(operands: list, segment: str, offset: int) -> InstructionResult:
        """
        Compile for LDR_LOC (Load from Local).

        Supports:
        - LDR_LOC REA, #0x1 (immediate)

        Args:
            operands: List of parsed operands
            segment: Current segment name
            offset: Current offset in segment
            
        Returns:
            InstructionResult with encoded instruction
        """
        if (len(operands) != 2):
            raise InstructionError(f"LDR_LOC requires 2 operands, got {len(operands)}")

        destType, destVal = operands[0]
        srcType, srcVal = operands[1]
        
        if (destType != OperandType.REGISTER):
            raise InstructionError("LDR_LOC destination must be a register")

        if (srcType != OperandType.IMMEDIATE):
            raise InstructionError("LDR_LOC source must be an immediate")

        opcode = INSTRUCTION_SET['LDR_LOC']
        bytecode = opcode | GenerateDestinationRegister(destVal)
        return InstructionResult(bytecode, pExtraWord=srcVal)

class LDR_ARGInstructionCompiler:
    """Compiler for LDR_ARG: load a register from an argument slot at [FP + imm]."""

    @staticmethod
    def Compile(operands: list, segment: str, offset: int) -> InstructionResult:
        """
        Compile for LDR_ARG (Load from argument slot).

        Supports:
        - LDR_ARG REA, #0x1 (immediate)

        Args:
            operands: List of parsed operands
            segment: Current segment name
            offset: Current offset in segment
            
        Returns:
            InstructionResult with encoded instruction
        """
        if (len(operands) != 2):
            raise InstructionError(f"LDR_ARG requires 2 operands, got {len(operands)}")

        destType, destVal = operands[0]
        srcType, srcVal = operands[1]
        
        if (destType != OperandType.REGISTER):
            raise InstructionError("LDR_ARG destination must be a register")

        if (srcType != OperandType.IMMEDIATE):
            raise InstructionError("LDR_ARG source must be an immediate")

        opcode = INSTRUCTION_SET['LDR_ARG']
        bytecode = opcode | GenerateDestinationRegister(destVal)
        return InstructionResult(bytecode, pExtraWord=srcVal)

class STR_LOCInstructionCompiler:
    """Compiler for STR_LOC: store a register to a local frame slot at [FP - imm]."""

    @staticmethod
    def Compile(operands: list, segment: str, offset: int) -> InstructionResult:
        """
        Compile STR_LOC instruction.

        Supports:
        - STR_LOC REA, #0x1 (register source, immediate offset)

        Args:
            operands: List of parsed operands
            segment: Current segment name
            offset: Current offset in segment

        Returns:
            InstructionResult with encoded instruction
        """
        if len(operands) != 2:
            raise InstructionError(f"STR_LOC requires 2 operands, got {len(operands)}")

        srcType, srcVal = operands[0]
        immType, immVal = operands[1]

        if srcType != OperandType.REGISTER:
            raise InstructionError("STR_LOC source must be a register")

        if immType != OperandType.IMMEDIATE:
            raise InstructionError("STR_LOC offset must be an immediate")

        opcode = INSTRUCTION_SET['STR_LOC']
        bytecode = opcode | GenerateSourceRegister(srcVal)
        return InstructionResult(bytecode, pExtraWord=immVal)


class STR_ARGInstructionCompiler:
    """Compiler for STR_ARG: store a register to an argument slot at [FP + imm]."""

    @staticmethod
    def Compile(operands: list, segment: str, offset: int) -> InstructionResult:
        """
        Compile STR_ARG instruction.

        Supports:
        - STR_ARG REA, #0x1 (register source, immediate offset)

        Args:
            operands: List of parsed operands
            segment: Current segment name
            offset: Current offset in segment

        Returns:
            InstructionResult with encoded instruction
        """
        if len(operands) != 2:
            raise InstructionError(f"STR_ARG requires 2 operands, got {len(operands)}")

        srcType, srcVal = operands[0]
        immType, immVal = operands[1]

        if srcType != OperandType.REGISTER:
            raise InstructionError("STR_ARG source must be a register")

        if immType != OperandType.IMMEDIATE:
            raise InstructionError("STR_ARG offset must be an immediate")

        opcode = INSTRUCTION_SET['STR_ARG']
        bytecode = opcode | GenerateSourceRegister(srcVal)
        return InstructionResult(bytecode, pExtraWord=immVal)


class SET_SP_RInstructionCompiler:
    """Compiler for SET_SP_R: copy a register's value into the stack pointer."""

    @staticmethod
    def Compile(operands: list, segment: str, offset: int) -> InstructionResult:
        """
        Compile SET_SP_R instruction.

        Supports:
        - SET_SP_R REX (register source — SP becomes the value of that register)

        Single-word instruction. Used by the C codegen's function epilogue to
        deallocate the entire local frame in one step via SET_SP_R FP.

        Args:
            operands: List of parsed operands
            segment: Current segment name (unused)
            offset: Current offset in segment (unused)

        Returns:
            InstructionResult with encoded instruction
        """
        if len(operands) != 1:
            raise InstructionError(f"SET_SP_R requires 1 operand, got {len(operands)}")

        srcType, srcVal = operands[0]
        if srcType != OperandType.REGISTER:
            raise InstructionError("SET_SP_R operand must be a register")

        opcode = INSTRUCTION_SET['SET_SP_R']
        bytecode = opcode | GenerateSourceRegister(srcVal)
        return InstructionResult(bytecode)


class LDIInstructionCompiler:
    """Compiler for LDI (Load Immediate) instruction."""
    
    @staticmethod
    def Compile(operands: list, segment: str, offset: int) -> InstructionResult:
        """
        Compile LDI instruction: LDI dest, src
        
        Supports:
        - LDI REA, #42  (immediate)
        - LDI REA, [0x1000]  (direct address)
        - LDI REA, symbol  (symbol reference)
        - LDI REA, REX  (register)
        
        Args:
            operands: List of parsed operands
            segment: Current segment name
            offset: Current offset in segment
            
        Returns:
            InstructionResult with encoded instruction
        """
        if len(operands) != 2:
            raise InstructionError(f"LDI requires 2 operands, got {len(operands)}")
        
        destType, destVal = operands[0]
        srcType, srcVal = operands[1]
        
        if destType != OperandType.REGISTER:
            raise InstructionError("LDI destination must be a register")
        
        # Immediate value
        if srcType == OperandType.IMMEDIATE:
            opcode = INSTRUCTION_SET['LDI'][0]
            bytecode = opcode | GenerateDestinationRegister(destVal)
            return InstructionResult(bytecode, pExtraWord=srcVal)
        
        # Direct address
        elif srcType == OperandType.DIRECT_ADDRESS:
            opcode = INSTRUCTION_SET['LDI'][1]
            bytecode = opcode | GenerateDestinationRegister(destVal)
            return InstructionResult(bytecode, pExtraWord=srcVal)
        
        # Symbol reference — non-bracketed loads the resolved address as a
        # literal (opcode[0]); bracketed loads the *value* at that address
        # (opcode[1], same as DIRECT_ADDRESS but with a relocation entry).
        elif srcType == OperandType.SYMBOL:
            opcode = INSTRUCTION_SET['LDI'][0]
            bytecode = opcode | GenerateDestinationRegister(destVal)
            relocation = {
                'segment': segment,
                'offset': offset + 1,
                'type': 'absolute',
                'symbol': srcVal
            }
            return InstructionResult(bytecode, pExtraWord=0, pRelocation=relocation)

        elif srcType == OperandType.DIRECT_ADDRESS_SYMBOL:
            opcode = INSTRUCTION_SET['LDI'][1]
            bytecode = opcode | GenerateDestinationRegister(destVal)
            relocation = {
                'segment': segment,
                'offset': offset + 1,
                'type': 'absolute',
                'symbol': srcVal
            }
            return InstructionResult(bytecode, pExtraWord=0, pRelocation=relocation)

        # Memory-config symbol reference — same opcode split as above.
        elif srcType == OperandType.MEMORY_CONFIG_SYMBOL:
            opcode = INSTRUCTION_SET['LDI'][0]
            bytecode = opcode | GenerateDestinationRegister(destVal)
            symbol_name = "$MEM$" + srcVal[1:]
            relocation = {
                'segment': segment,
                'offset': offset + 1,
                'type': 'absolute',
                'symbol': symbol_name
            }
            return InstructionResult(bytecode, pExtraWord=0, pRelocation=relocation)

        elif srcType == OperandType.DIRECT_ADDRESS_MEMORY_CONFIG_SYMBOL:
            opcode = INSTRUCTION_SET['LDI'][1]
            bytecode = opcode | GenerateDestinationRegister(destVal)
            symbol_name = "$MEM$" + srcVal[1:]
            relocation = {
                'segment': segment,
                'offset': offset + 1,
                'type': 'absolute',
                'symbol': symbol_name
            }
            return InstructionResult(bytecode, pExtraWord=0, pRelocation=relocation)

        # Register
        elif srcType == OperandType.REGISTER:
            opcode = INSTRUCTION_SET['LDI'][2]
            bytecode = (opcode | 
                       GenerateSourceRegister(srcVal) | 
                       GenerateDestinationRegister(destVal))
            return InstructionResult(bytecode)
        
        else:
            raise InstructionError(f"Invalid LDI source operand type: {srcType}")


class STRInstructionCompiler:
    """Compiler for STR (Store) instruction."""
    
    @staticmethod
    def Compile(pOperands: list, pSegment: str, pOffset: int) -> InstructionResult:
        """
        Compile STR instruction: STR dest, src
        
        Supports:
        - STR [0x1000], REA  (direct address)
        - STR symbol, REA  (symbol reference)
        - STR REX, REA  (register indirect)
        
        Args:
            operands: List of parsed operands
            segment: Current segment name
            offset: Current offset in segment
            
        Returns:
            InstructionResult with encoded instruction
        """
        if len(pOperands) != 2:
            raise InstructionError(f"STR requires 2 operands, got {len(pOperands)}")
        
        destType, destVal = pOperands[0]
        srcType, srcVal = pOperands[1]
        
        if srcType != OperandType.REGISTER:
            raise InstructionError("STR source must be a register")
        
        # Direct address
        if destType == OperandType.DIRECT_ADDRESS:
            opcode = INSTRUCTION_SET['STR'][0]
            bytecode = opcode | GenerateSourceRegister(srcVal)
            return InstructionResult(bytecode, pExtraWord=destVal)
        
        # Symbol reference. STR's destination is always an address, so the
        # bracketed `[label]` form is semantically identical to bare `label`
        # — both store into the linker-resolved address.
        elif destType in (OperandType.SYMBOL, OperandType.DIRECT_ADDRESS_SYMBOL):
            opcode = INSTRUCTION_SET['STR'][0]
            bytecode = opcode | GenerateSourceRegister(srcVal)
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': destVal
            }
            return InstructionResult(bytecode, pExtraWord=0, pRelocation=relocation)

        # Memory config symbol reference (bracketed and non-bracketed: same).
        elif destType in (OperandType.MEMORY_CONFIG_SYMBOL,
                          OperandType.DIRECT_ADDRESS_MEMORY_CONFIG_SYMBOL):
            opcode = INSTRUCTION_SET['STR'][0]
            bytecode = opcode | GenerateSourceRegister(srcVal)
            # Use a special prefix to mark this as a memory config symbol
            symbol_name = "$MEM$" + destVal[1:]  # Replace $ with $MEM$ marker
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': symbol_name
            }
            return InstructionResult(bytecode, pExtraWord=0, pRelocation=relocation)
        
        # Register indirect
        elif destType == OperandType.REGISTER:
            opcode = INSTRUCTION_SET['STR'][1]
            bytecode = (opcode | 
                       GenerateSourceRegister(srcVal) | 
                       GenerateDestinationRegister(destVal))
            return InstructionResult(bytecode)
        
        else:
            raise InstructionError(
                "STR destination must be direct address, symbol, or register"
            )


class ControlFlowInstructionCompiler:
    """Compiler for control flow instructions (JP, JPZ, JPC, CALL)."""
    
    @staticmethod
    def Compile(pMnemonic: str, pOperands: list, pSegment: str, pOffset: int) -> InstructionResult:
        """
        Compile control flow instructions.

        Addressing modes (encoded as three distinct opcodes per mnemonic):
        - JP #0x1000   — immediate: branch to literal address 0x1000     -> opcode[0]
        - JP my_label  — symbol:    branch to address resolved by linker -> opcode[0]
        - JP REA       — register:  branch to address held in REA        -> opcode[1]
        - JP [0x1000]  — memory-indirect: load target from RAM[0x1000],
                         then branch to that value                       -> opcode[2]
        """
        if len(pOperands) != 1:
            raise InstructionError(f"{pMnemonic} requires 1 operand, got {len(pOperands)}")

        opType, opVal = pOperands[0]

        # Symbol reference — linker resolves to absolute address (immediate form).
        if opType == OperandType.SYMBOL:
            opcode = INSTRUCTION_SET[pMnemonic][0]
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': opVal
            }
            return InstructionResult(opcode, pExtraWord=0, pRelocation=relocation)

        # Memory-config symbol — same immediate form, with the $MEM$ marker.
        elif opType == OperandType.MEMORY_CONFIG_SYMBOL:
            opcode = INSTRUCTION_SET[pMnemonic][0]
            symbol_name = "$MEM$" + opVal[1:]
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': symbol_name
            }
            return InstructionResult(opcode, pExtraWord=0, pRelocation=relocation)

        # Immediate — literal absolute address baked into the extra word.
        elif opType == OperandType.IMMEDIATE:
            opcode = INSTRUCTION_SET[pMnemonic][0]
            return InstructionResult(opcode, pExtraWord=opVal)

        # Memory-indirect — extra word is the RAM address holding the target.
        elif opType == OperandType.DIRECT_ADDRESS:
            opcode = INSTRUCTION_SET[pMnemonic][2]
            return InstructionResult(opcode, pExtraWord=opVal)

        # Memory-indirect via symbol — linker fills in the RAM address; CPU
        # then reads the target value from that location. `CALL [my_label]`.
        elif opType == OperandType.DIRECT_ADDRESS_SYMBOL:
            opcode = INSTRUCTION_SET[pMnemonic][2]
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': opVal
            }
            return InstructionResult(opcode, pExtraWord=0, pRelocation=relocation)

        # Memory-indirect via memory-config symbol — `CALL [$TTYOwner.Start]`.
        elif opType == OperandType.DIRECT_ADDRESS_MEMORY_CONFIG_SYMBOL:
            opcode = INSTRUCTION_SET[pMnemonic][2]
            symbol_name = "$MEM$" + opVal[1:]
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': symbol_name
            }
            return InstructionResult(opcode, pExtraWord=0, pRelocation=relocation)

        # Register-direct — target address is in the named register.
        elif opType == OperandType.REGISTER:
            opcode = INSTRUCTION_SET[pMnemonic][1]
            bytecode = opcode | GenerateSourceRegister(opVal)
            return InstructionResult(bytecode)

        else:
            raise InstructionError(f"Invalid {pMnemonic} operand type: {opType}")


class StackInstructionCompiler:
    """Compiler for stack instructions (PUSH, POP)."""
    
    @staticmethod
    def CompilePush(pOperands: list, pSegment: str, pOffset: int) -> InstructionResult:
        """
        Compile PUSH instruction: PUSH src
        
        Supports:
        - PUSH REA  (register)
        - PUSH #42  (immediate)
        - PUSH symbol  (symbol reference)
        
        Args:
            operands: List of parsed operands
            segment: Current segment name
            offset: Current offset in segment
            
        Returns:
            InstructionResult with encoded instruction
        """
        if len(pOperands) != 1:
            raise InstructionError(f"PUSH requires 1 operand, got {len(pOperands)}")
        
        srcType, srcVal = pOperands[0]
        
        # Register
        if srcType == OperandType.REGISTER:
            opcode = INSTRUCTION_SET['PUSH'][0]
            bytecode = opcode | GenerateSourceRegister(srcVal)
            return InstructionResult(bytecode)
        
        # Immediate
        elif srcType == OperandType.IMMEDIATE:
            opcode = INSTRUCTION_SET['PUSH'][1]
            return InstructionResult(opcode, pExtraWord=srcVal)
        
        # Symbol reference (bracketed and non-bracketed forms both push the
        # symbol's resolved address — PUSH has no "push value at address" form).
        elif srcType in (OperandType.SYMBOL, OperandType.DIRECT_ADDRESS_SYMBOL):
            opcode = INSTRUCTION_SET['PUSH'][1]
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': srcVal
            }
            return InstructionResult(opcode, pExtraWord=0, pRelocation=relocation)

        # Memory config symbol reference (bracketed and non-bracketed: same).
        elif srcType in (OperandType.MEMORY_CONFIG_SYMBOL,
                         OperandType.DIRECT_ADDRESS_MEMORY_CONFIG_SYMBOL):
            opcode = INSTRUCTION_SET['PUSH'][1]
            # Use a special prefix to mark this as a memory config symbol
            symbol_name = "$MEM$" + srcVal[1:]  # Replace $ with $MEM$ marker
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': symbol_name
            }
            return InstructionResult(opcode, pExtraWord=0, pRelocation=relocation)

        else:
            raise InstructionError("PUSH operand must be register, immediate, or symbol")
    
    @staticmethod
    def CompilePop(pOperands: list) -> InstructionResult:
        """
        Compile POP instruction: POP dest
        
        Args:
            operands: List of parsed operands
            
        Returns:
            InstructionResult with encoded instruction
        """
        if len(pOperands) != 1:
            raise InstructionError(f"POP requires 1 operand, got {len(pOperands)}")
        
        destType, destVal = pOperands[0]
        
        if destType != OperandType.REGISTER:
            raise InstructionError("POP operand must be a register")
        
        opcode = INSTRUCTION_SET['POP']
        bytecode = opcode | GenerateDestinationRegister(destVal)
        return InstructionResult(bytecode)


class SystemInstructionCompiler:
    """Compiler for system instructions (SET_SP, GET_SP, GET_PC, SET_IVR, etc.)."""
    
    @staticmethod
    def CompileSetSP(pOperands: list, pSegment: str, pOffset: int) -> InstructionResult:
        """Compile SET_SP instruction."""
        if len(pOperands) != 1:
            raise InstructionError(f"SET_SP requires 1 operand, got {len(pOperands)}")
        
        srcType, srcVal = pOperands[0]
        opcode = INSTRUCTION_SET['SET_SP']
        
        if srcType == OperandType.IMMEDIATE:
            return InstructionResult(opcode, pExtraWord=srcVal)
        elif srcType in (OperandType.SYMBOL, OperandType.DIRECT_ADDRESS_SYMBOL):
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': srcVal
            }
            return InstructionResult(opcode, pExtraWord=0, pRelocation=relocation)
        elif srcType in (OperandType.MEMORY_CONFIG_SYMBOL,
                         OperandType.DIRECT_ADDRESS_MEMORY_CONFIG_SYMBOL):
            # Use a special prefix to mark this as a memory config symbol
            symbol_name = "$MEM$" + srcVal[1:]  # Replace $ with $MEM$ marker
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': symbol_name
            }
            return InstructionResult(opcode, pExtraWord=0, pRelocation=relocation)
        else:
            raise InstructionError("SET_SP operand must be immediate, symbol, or memory config symbol")
    
    @staticmethod
    def CompileGetSP(pOperands: list) -> InstructionResult:
        """Compile GET_SP instruction."""
        if len(pOperands) != 1:
            raise InstructionError(f"GET_SP requires 1 operand, got {len(pOperands)}")
        
        destType, destVal = pOperands[0]
        
        if destType != OperandType.REGISTER:
            raise InstructionError("GET_SP operand must be a register")
        
        opcode = INSTRUCTION_SET['GET_SP']
        bytecode = opcode | GenerateDestinationRegister(destVal)
        return InstructionResult(bytecode)
    
    @staticmethod
    def CompileGetPC(pOperands: list) -> InstructionResult:
        """Compile GET_PC instruction."""
        if len(pOperands) != 1:
            raise InstructionError(f"GET_PC requires 1 operand, got {len(pOperands)}")
        
        destType, destVal = pOperands[0]
        
        if destType != OperandType.REGISTER:
            raise InstructionError("GET_PC operand must be a register")
        
        opcode = INSTRUCTION_SET['GET_PC']
        bytecode = opcode | GenerateDestinationRegister(destVal)
        return InstructionResult(bytecode)
    
    @staticmethod
    def CompileSetIVR(pOperands: list, pSegment: str, pOffset: int) -> InstructionResult:
        """Compile SET_IVR instruction."""
        if len(pOperands) != 1:
            raise InstructionError(f"SET_IVR requires 1 operand, got {len(pOperands)}")
        
        srcType, srcVal = pOperands[0]
        opcode = INSTRUCTION_SET['SET_IVR']
        
        if srcType == OperandType.IMMEDIATE:
            return InstructionResult(opcode, pExtraWord=srcVal)
        elif srcType in (OperandType.SYMBOL, OperandType.DIRECT_ADDRESS_SYMBOL):
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': srcVal
            }
            return InstructionResult(opcode, pExtraWord=0, pRelocation=relocation)
        elif srcType in (OperandType.MEMORY_CONFIG_SYMBOL,
                         OperandType.DIRECT_ADDRESS_MEMORY_CONFIG_SYMBOL):
            # Use a special prefix to mark this as a memory config symbol
            symbol_name = "$MEM$" + srcVal[1:]  # Replace $ with $MEM$ marker
            relocation = {
                'segment': pSegment,
                'offset': pOffset + 1,
                'type': 'absolute',
                'symbol': symbol_name
            }
            return InstructionResult(opcode, pExtraWord=0, pRelocation=relocation)
        else:
            raise InstructionError("SET_IVR operand must be immediate, symbol, or memory config symbol")
    
    @staticmethod
    def CompileGetIntID(pOperands: list) -> InstructionResult:
        """Compile GET_INT_ID instruction."""
        if len(pOperands) != 1:
            raise InstructionError(f"GET_INT_ID requires 1 operand, got {len(pOperands)}")
        
        destType, destVal = pOperands[0]
        
        if destType != OperandType.REGISTER:
            raise InstructionError("GET_INT_ID operand must be a register")
        
        opcode = INSTRUCTION_SET['GET_INT_ID']
        bytecode = opcode | GenerateDestinationRegister(destVal)
        return InstructionResult(bytecode)
    
