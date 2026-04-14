; =============================================================================
; Shell - Command Processor
; =============================================================================
; Main event loop for the OS. Polls for keyboard input and dispatches
; commands based on keycode values.
;
; Since the display is 64x64 pixels, the shell uses visual feedback
; rather than text. Key presses trigger different visual responses.
;
; Key mapping (keycodes depend on hardware wiring):
;   1 (0x31) = Run color demo pattern
;   2 (0x32) = Run animation demo
;   3 (0x33) = Clear screen
;   4 (0x34) = Show system info (boot logo)
;   5 (0x35) = Ray tracing demo
;   0 (0x30) = Shutdown system
; =============================================================================

!IMPORT "../drivers/Keyboard.asm" as Keyboard
!IMPORT "../drivers/Video.asm" as Video
!IMPORT "../programs/Demo.asm" as Demo

.Shell

Main:
    PUSH REA
    PUSH REB
    PUSH REC

ShellLoop:
    ; Check if system_state == 1 (shutdown requested)
    LDI REB, $OSData.Start
    LDI REC, #4
    ADD REB, REC               ; REB -> OSData+4 (system_state)
    LDI REA, [REB]
    LDI REC, #1
    SUB REA, REC
    JPZ ShellExit              ; shutdown requested

    ; Check for available key
    CALL Keyboard.HasKey
    LDI REC, #1
    SUB REA, REC
    JPZ ShellProcessKey        ; key available

    ; No key: continue polling
    JP ShellLoop

ShellProcessKey:
    CALL Keyboard.ReadKey      ; REA = keycode

    ; --- Dispatch based on keycode ---

    ; Check for '1' (0x31) - color pattern demo
    MOV REB, REA
    LDI REC, #0x31
    SUB REB, REC
    JPZ ShellRunColorDemo

    ; Check for '2' (0x32) - animation demo
    MOV REB, REA
    LDI REC, #0x32
    SUB REB, REC
    JPZ ShellRunAnimDemo

    ; Check for '3' (0x33) - clear screen
    MOV REB, REA
    LDI REC, #0x33
    SUB REB, REC
    JPZ ShellClearScreen

    ; Check for '4' (0x34) - show boot logo
    MOV REB, REA
    LDI REC, #0x34
    SUB REB, REC
    JPZ ShellShowInfo

    ; Check for '5' (0x35) - ray trace demo
    MOV REB, REA
    LDI REC, #0x35
    SUB REB, REC
    JPZ ShellRunRayTrace

    ; Check for '0' (0x30) - shutdown
    MOV REB, REA
    LDI REC, #0x30
    SUB REB, REC
    JPZ ShellShutdown

    ; Unknown key: flash a red pixel at (1,1) as feedback
    PUSH REA
    LDI REA, #1
    LDI REB, #1
    LDI REC, #0x0C            ; light red
    CALL Video.WritePixel
    POP REA

    JP ShellLoop

; --- Command handlers ---

ShellRunColorDemo:
    CALL Demo.ColorPattern
    JP ShellLoop

ShellRunAnimDemo:
    CALL Demo.DiagonalWipe
    JP ShellLoop

ShellRunRayTrace:
    CALL Demo.RayTrace
    JP ShellLoop

ShellClearScreen:
    CALL Video.ClearScreen
    ; Draw ready indicator
    LDI REA, #60
    LDI REB, #60
    LDI REC, #0x0E            ; yellow = ready
    CALL Video.WritePixel
    JP ShellLoop

ShellShowInfo:
    CALL Video.ClearScreen
    CALL Video.DrawBootLogo
    CALL Video.DrawMenu
    JP ShellLoop

ShellShutdown:
    ; Show shutdown indicator: red square in center
    CALL Video.ClearScreen
    LDI REA, #31
    LDI REB, #31
    LDI REC, #0x0C            ; red center pixel
    CALL Video.WritePixel
    LDI REA, #32
    LDI REB, #31
    CALL Video.WritePixel
    LDI REA, #31
    LDI REB, #32
    CALL Video.WritePixel
    LDI REA, #32
    LDI REB, #32
    CALL Video.WritePixel

    ; Set system_state = 1 (shutdown)
    LDI REB, $OSData.Start
    LDI REC, #4
    ADD REB, REC
    LDI REA, #1
    STR [REB], REA
    JP ShellLoop

ShellExit:
    POP REC
    POP REB
    POP REA
    RTS
