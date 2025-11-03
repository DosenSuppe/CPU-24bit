# micro instructions
INSTRUCTION_LOAD = 1 << 0
INSTRUCTION_END = 1 << 1

PC_INCREMENT = 1 << 2
PC_ADDRESS_OUT = 1 << 3
PC_DATA_OUT = 1 << 4
PC_WRITE = 1 << 5

SP_INCREMENT = 1 << 6
SP_DECREMENT = 1 << 7
SP_ADDREESS_OUT = 1 << 8
SP_DATA_OUT = 1 << 9
SP_WRITE = 1 << 10

ALU_OPERATION = 1 << 11 # from bit 11 to bit 14
ALU_OUT = 1 << 15

GPR_ADDRESS_OUT = 1 << 16
GPR_DATA_OUT = 1 << 17
GPR_WRITE = 1 << 18

RAM_READ = 1 << 19
RAM_WRITE = 1 << 20

INTEERRUPT_REQUEST_ACKNOWLEDGE = 1 << 21
BUS_GRANT = 1 << 22

HALT = 1 << 23



def GenerateALUOperation(pOperation: int) -> int:
    return (pOperation & 0x7) << 12



def GenerateRegister(pRegister: int) -> int:
    return (pRegister & 0x1F) << 17

