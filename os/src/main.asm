.SetUp
SET_IVR #0x30       ; Start of Reset-Vector
SET_SP  #0xDFFFFF   ; Set Stack Pointer

JP InitKernel

.InterruptHandler
ADD REC, REB
RTI

.Kernel
InitKernel:
    


HALT
