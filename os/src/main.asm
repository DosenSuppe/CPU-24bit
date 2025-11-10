.SetUp
SET_IVR #0x30       ; Start of Reset-Vector
SET_SP  #0xDFFFFF   ; Set Stack Pointer

JP InitKernel

.InterruptHandler
PUSH REB

LDI REB, #0x1
SUB REA, REB, REX

JPZ Print_CALL

InterruptHandled:
POP REB
RTI

.Kernel
InitKernel:


INT_Print_CALL:
    CALL Print
    JP InterruptHandled

Print:
    RTS

HALT
