!IMPORT "drivers/ButtonDriver.asm" as ButtonDriver

.SetUp
SET_IVR ResetVector     ; Start of Reset-Vector
SET_SP  Stack           ; Set Stack Pointer

JP InitKernel

.ResetVector
JP ButtonDriver.HandleInterrupt


.Kernel
InitKernel:
    LDI REB, #0x1

    JP KernalLoop

KernalLoop: ; keeping the CPU busy
    ADD REA, REB
    JP KernalLoop

HALT
