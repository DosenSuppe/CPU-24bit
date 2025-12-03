; =============================================================================
; Keyboard Driver
; =============================================================================
; Handles keyboard interrupts from device 0.
; Reads the keycode via GET_INT_DATA and stores it in the OS data area
; so the shell can pick it up.
;
; OSData layout used:
;   +0 : key_available flag
;   +1 : last_keycode
; =============================================================================

.KeyboardDriver

; Called from the interrupt handler when a keyboard interrupt fires.
OnInterrupt:
    PUSH REA
    PUSH REB
    PUSH REC

    GET_INT_DATA REA           ; read the keycode from the PIC

    ; Store keycode at OSData+1
    LDI REB, $OSData.Start
    LDI REC, #1
    ADD REB, REC               ; REB = OSData.Start + 1
    STR [REB], REA             ; store keycode

    ; Set key_available flag at OSData+0
    LDI REB, $OSData.Start
    LDI REA, #1
    STR [REB], REA             ; key_available = 1

    POP REC
    POP REB
    POP REA
    RTS

; -----------------------------------------------------------------------------
; ReadKey - Blocking read: waits until a key is available, returns it in REA.
; Clears the key_available flag after reading.
; Returns: REA = keycode
; -----------------------------------------------------------------------------
ReadKey:
    PUSH REB
    PUSH REC

ReadKeyWait:
    LDI REB, $OSData.Start
    LDI REA, [REB]             ; load key_available flag
    LDI REC, #1
    SUB REA, REC
    JPZ ReadKeyReady           ; if flag == 1, a key is available

    JP ReadKeyWait             ; busy-wait

ReadKeyReady:
    ; Read the keycode from OSData+1
    LDI REB, $OSData.Start
    LDI REC, #1
    ADD REB, REC
    LDI REA, [REB]             ; REA = keycode

    ; Clear the key_available flag
    LDI REB, $OSData.Start
    LDI REC, #0
    STR [REB], REC             ; key_available = 0

    POP REC
    POP REB
    RTS

; -----------------------------------------------------------------------------
; HasKey - Non-blocking check: returns 1 in REA if a key is available, else 0.
; -----------------------------------------------------------------------------
HasKey:
    PUSH REB

    LDI REB, $OSData.Start
    LDI REA, [REB]             ; REA = key_available (0 or 1)

    POP REB
    RTS
