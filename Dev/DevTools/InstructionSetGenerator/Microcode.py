from Registers import *


# micro instructions
INSTRUCTION_LOAD = 1 << 0
ENABLE_PC = 1 << 1
RAM_ADDRESS_LOAD = 1 << 2
RAM_READ = 1 << 3
RAM_WRITE = 1 << 4


EXPANSION_PORT_STORE = 1 << 8
EXPANSION_PORT_LOAD = 1 << 9

HALT = 1 << 10
INSTRUCTION_READ = 1 << 11

def GenerateALUOperation(pOperation: Register | ExpasionPortRegister) -> int:
    return (pOperation.value & 0x7) << 12

ENABLE_RAM_OUTPUT = 1 << 15
ENABLE_SOURCE_REGISTER = 1 << 16

def GenerateDestinationRegister(pRegister: Register | ExpasionPortRegister) -> int:
    return (pRegister.value & 0x1F) << 17

REGISTER_LOAD = 1 << 22
REGISTER_STORE = 1 << 23
