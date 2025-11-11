!IMPORT "drivers/ButtonDriver.asm" as ButtonDriver

.SetUp
SET_IVR ResetVector     ; Start of Reset-Vector
SET_SP  Stack           ; Set Stack Pointer

JP InitKernel

.ResetVector
CALL ButtonDriver.HandleInterrupt
RTI

.Kernel
InitKernel:
    JP KernalLoop

KernalLoop: ; keeping the CPU busy
    JP KernalLoop

HALT
