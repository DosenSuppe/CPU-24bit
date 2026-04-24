; =============================================================================
; DosB OS - Kernel Entry Point
; =============================================================================
; A simple operating system for the 24-bit CPU.
; Provides interrupt handling, keyboard input, video output, and a shell.
; =============================================================================

!IMPORT "./system/Interrupt.asm" as Interrupt
!IMPORT "./drivers/Video.asm" as Video
!IMPORT "./drivers/Keyboard.asm" as Keyboard
!IMPORT "./shell/Shell.asm" as Shell

.Kernel

Boot:
    SET_SP $Stack.Start

    ; Set interrupt vector to our dispatcher
    SET_IVR Interrupt.Handler

    ; Initialize OS data area (clear flags)
    CALL InitOSData

    ; Clear screen
    CALL Video.ClearScreen

    CALL Video.PackPixel

    ; Draw boot screen
    CALL Video.DrawBootLogo
    CALL Video.DrawMenu

    ; Enter the shell main loop
    CALL Shell.Main

    ; If shell returns, halt the system
    HALT

; -----------------------------------------------------------------------------
; InitOSData - Zero out OS data fields
; OSData layout:
;   +0 : key_available flag (0=no key, 1=key ready)
;   +1 : last_keycode
;   +2 : cursor_x (0-15)
;   +3 : cursor_y (0-15)
;   +4 : system_state (0=running, 1=shutdown requested)
; -----------------------------------------------------------------------------
InitOSData:
    PUSH REA
    PUSH REB
    PUSH REC

    LDI REA, #0              ; value to store (zero)
    LDI REB, $OSData.Start   ; base address
    LDI REC, #1              ; increment

    STR [REB], REA            ; +0 key_available = 0
    ADD REB, REC
    STR [REB], REA            ; +1 last_keycode = 0
    ADD REB, REC
    STR [REB], REA            ; +2 cursor_x = 0
    ADD REB, REC
    STR [REB], REA            ; +3 cursor_y = 0
    ADD REB, REC
    STR [REB], REA            ; +4 system_state = 0

    POP REC
    POP REB
    POP REA
    RTS
