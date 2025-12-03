"""Instruction set definitions and encoding utilities."""


def GenerateARegister(pRegister: int) -> int:
    """Encode a register value for the source register field."""
    return (pRegister & 0x1F) << 8


def GenerateBRegister(pRegister: int) -> int:
    """Encode a register value for the destination register field."""
    return (pRegister & 0x1F) << 12

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
    'GET_INT_ID': 0x24,
    'GET_INT_DATA': 0x25,
    'RTI': 0xFE,
    'INT': 0xFF
}

# Instruction categories for easier classification
SIMPLE_INSTRUCTIONS = {'NOP', 'HALT', 'RTS', 'RTI', 'INT'}
ALU_BINARY_OPERATIONS = {'ADD', 'SUB', 'MUL', 'DIV', 'SHL', 'SHR', 'NAND', 'AND', 'OR', 'XOR', 'NOR'}
ALU_UNARY_OPERATIONS = {'NOT'}
CONTROL_FLOW_INSTRUCTIONS = {'JP', 'JPZ', 'JPC', 'CALL'}
STACK_INSTRUCTIONS = {'PUSH', 'POP'}
