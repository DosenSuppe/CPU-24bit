from enum import Enum

class ALUOperations(Enum):
    Add = 0x0
    Sub = 0x1
    Mul = 0x2
    Div = 0x3
    Shift = 0x4
    And = 0x5
    Or = 0x6
    Xor = 0x7

class MicroInstructions(Enum):
    RegisterLoad = 0x400000
    RegisterStore = 0x800000

    Halt = 0x400
    InstructionRead = 0x600
    InstructionLoad = 0x1

    EnablePC = 0x2

    RAM_Address_Load = 0x4
    RAM_Read = 0x8
    RAM_Write = 0x10

    # Outputs TODO

    # Inputs TODO


class Registers(Enum):
    # ALU Registers
    REA = 0x0
    REB = 0x1
    ACC = 0x2

    # General Purpose Registers
    REZ = 0x3
    REY = 0x4
    REX = 0x5
    REW = 0x6
    REV = 0x7
    REU = 0x8
    RET = 0x9
    RES = 0xA
    RER = 0xB
    REQ = 0xC
    REP = 0xD

    # System Registers (Stack Pointer, Program Counter)
    SP = 0xE
    PC = 0xF



