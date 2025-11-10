!IMPORT "drivers/JoystickDriver.asm" as JoystickDriver

.SetUp
LDI REA, #0xE00000
LDI REB, #1
STR [REA], REB    ; Enable Joystick Interrupt

SET_IVR #0x30       ; Start of Reset-Vector
SET_SP  #0xDFFFFF   ; Set Stack Pointer

JP InitKernel


.InterruptHandler
;PUSH REB            ; saving REB and REX for later restoration
;PUSH REX
;PUSH REA 

; checking the interrupt source
;LDI REA, [#0xE00000]    ; location of the Joystick interrupt status register
;LDI REB, #0x1           
;SUB REA, REB, REX

CALL Interrupt_Joystick

HandledInterrupt:
;POP REA
;POP REX
;POP REB
RTI

Interrupt_Joystick:
    CALL JoystickDriver.HandleInterrupt
    JP HandledInterrupt

.Kernel
InitKernel:
    JP KernalLoop

KernalLoop:
    NOP
    JP KernalLoop


HALT
