.SetUp
SET_IVR #0x20   ; Start of Reset-Vector
SET_SP #0x33   ; Set Stack Pointer

JP Main

.InterruptHandler
LDI REB, #0x123
RTI

.Code

Main:
    LDI REA, #0x1

Counter:
    ADD REA, REA

    JP Counter

HALT
