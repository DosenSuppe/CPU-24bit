"""Instruction set definitions and encoding utilities."""


def GenerateSourceRegister(pRegister: int) -> int:
    """Encode a register value for the source register field."""
    return (pRegister & 0x1F) << 8


def GenerateDestinationRegister(pRegister: int) -> int:
    """Encode a register value for the destination register field."""
    return (pRegister & 0x1F) << 12


def GenerateALUAInput(pRegister: int) -> int:
    """Encode a register value for the ALU A input field."""
    return (pRegister & 0xF) << 16


def GenerateALUBInput(pRegister: int) -> int:
    """Encode a register value for the ALU B input field."""
    return (pRegister & 0xF) << 20

# Instruction opcodes
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
    # Branch instructions. Each maps to a 3-element list:
    #   [0] immediate / symbol absolute address  (JP #0x1000, JP my_label)
    #   [1] register-direct                      (JP REA)
    #   [2] memory-indirect                      (JP [0x1000]  — load target
    #                                             address from RAM at 0x1000,
    #                                             then branch to that value)
    'JP':       [0x14, 0x15, 0x3D],
    'JPZ':      [0x16, 0x17, 0x3E],
    'JPC':      [0x18, 0x19, 0x3F],
    'CALL':     [0x1A, 0x1B, 0x40],
    'RTS': 0x1C,
    'PUSH': [0x1D, 0x1E],
    'POP': 0x1F,
    'SET_SP': 0x20,
    'GET_SP': 0x21,
    'GET_PC': 0x22,
    'SET_IVR': 0x23,
    'GET_INT_ID': 0x24,

    'CALL_EQ':  [0x25, 0x26, 0x41],
    'CALL_LT':  [0x27, 0x28, 0x42],
    'CALL_GT':  [0x29, 0x2A, 0x43],
    'CALL_NEQ': [0x34, 0x35, 0x44],
    'JP_EQ':    [0x2B, 0x2C, 0x45],
    'JP_LT':    [0x2D, 0x2E, 0x46],
    'JP_GT':    [0x2F, 0x30, 0x47],
    'JP_NEQ':   [0x32, 0x33, 0x48],

    'LDR_LOC': 0x36,
    'STR_LOC': 0x37,
    'LDR_ARG': 0x38,
    'STR_ARG': 0x39,

    # TODO
    # 'ADDR_LOC': 0x3A,
    # 'ADDR_ARG': 0x3B,

    'SET_SP_R': 0x3C,
    
    'CMP': 0x31,   
    
    'RTI': 0xFE,
    'INT': 0xFF
}

# Instruction categories for easier classification
SIMPLE_INSTRUCTIONS = {'NOP', 'HALT', 'RTS', 'RTI', 'INT'}
ALU_BINARY_OPERATIONS = {'ADD', 'SUB', 'MUL', 'DIV', 'SHL', 'SHR', 'NAND', 'AND', 'OR', 'XOR', 'NOR'}
ALU_UNARY_OPERATIONS = {'NOT'}
CONTROL_FLOW_INSTRUCTIONS = {'JP', 'JPZ', 'JPC', 'CALL', 'CALL_EQ', 'CALL_LT', 'CALL_GT', 'JP_EQ', 'JP_LT', 'JP_GT', 'JP_NEQ', 'CALL_NEQ'}
STACK_INSTRUCTIONS = {'PUSH', 'POP'}
