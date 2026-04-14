; =============================================================================
; Interrupt Dispatcher
; =============================================================================
; Called by the CPU when any interrupt occurs (hardware or software INT).
; Dispatches to the appropriate driver based on device ID.
;
; Device ID assignment:
;   0 = Reserved
;   1 = Reserved
;   2 = Keyboard (PIC Device2_In)
;   3-6 = Available for expansion
;   Software INT = no device ID; used for syscalls
; =============================================================================

!IMPORT "../drivers/Keyboard.asm" as Keyboard

.InterruptHandler

Handler:
    PUSH REA
    PUSH REB
    PUSH REC

    GET_INT_ID REA             ; get the device ID that caused this interrupt

    ; --- Check for Keyboard (device 2) ---
    MOV REB, REA
    LDI REC, #2
    SUB REB, REC
    JPZ DispatchKeyboard

    ; --- Check for device 3 (future) ---
    MOV REB, REA
    LDI REC, #3
    SUB REB, REC
    JPZ DispatchDevice1

    ; --- Unknown or software interrupt: fall through ---
    JP InterruptDone

DispatchKeyboard:
    CALL Keyboard.OnInterrupt
    JP InterruptDone

DispatchDevice1:
    ; Reserved for future device 3
    JP InterruptDone

InterruptDone:
    POP REC
    POP REB
    POP REA
    RTI
