# micro instructions
INSTRUCTION_LOAD = 1 << 0
INSTRUCTION_END = 1 << 1

ALU_ENABLE = 1 << 6

GPR_READ = 1 << 7
GPR_WRITE = 1 << 8
GPR_AS_ADDRESS = 1 << 9

IRQ_PROMPT = 1 << 37
IRQ_ACK = 1 << 38
HALT = 1 << 39

def GenerateALUOperation(pOperation: int) -> int:
    return (pOperation & 0xF) << 2
