!IMPORT "drivers/ButtonDriver.asm" as ButtonDriver
!IMPORT "programs/pong.asm" as pong

.SetUp
SET_IVR ResetVector     ; Start of Reset-Vector
SET_SP  Stack           ; Set Stack Pointer

JP InitKernel

.ResetVector
JP ButtonDriver.HandleInterrupt

.Kernel
InitKernel:
    JP KernalLoop

KernalLoop: ; keeping the CPU busy
    CALL pong.Main
    
    HALT

