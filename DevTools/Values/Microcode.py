# micro instructions
INSTRUCTION_LOAD = 1 << 0
INSTRUCTION_END = 1 << 1

PC_INCREMENT = 1 << 2
PC_ADDRESS_OUT = 1 << 3
PC_DATA_OUT = 1 << 4
PC_WRITE = 1 << 5

SP_INCREMENT = 1 << 6
SP_DECREMENT = 1 << 7
SP_ADDRESS_OUT = 1 << 8
SP_DATA_OUT = 1 << 9
SP_WRITE = 1 << 10

ALU_OPERATION = 1 << 11 # from bit 11 to bit 14
ALU_OUT = 1 << 15

GPR_ADDRESS_OUT = 1 << 16
GPR_DATA_OUT = 1 << 17
GPR_WRITE = 1 << 18

RAM_READ = 1 << 19
RAM_WRITE = 1 << 20

MAR_WRITE = 1 << 21
MAR_SOURCE_SELECT = 1 << 22  # 0 = from Address-Bus, 1 = from Data-Bus

GPR_B_ADDRESS_OUT = 1 << 23
GPR_B_DATA_OUT = 1 << 24
GPR_B_WRITE = 1 << 25

INTERRUPT_CHECK = 1 << 26
IVR_WRITE = 1 << 27
IVR_OUT = 1 << 28
INTERRUPT_REQUEST_ACKNOWLEDGE = 1 << 29
BUS_GRANT = 1 << 30

HALT = 1 << 31

FR_DATA_OUT = 1 << 37
FR_WRITE = 1 << 38
FR_WRITE_FROM_RAM = 1 << 39

def GenerateALUOperation(pOperation: int) -> int:
    return (pOperation & 0xF) << 11

def GenerateRegister(pRegister: int) -> int:
    return (pRegister & 0x1F) << 17

