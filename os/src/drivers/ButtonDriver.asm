.ButtonDriver
HandleInterrupt:
    PUSH REX
    PUSH REY
    PUSH REZ

    GET_INT_DATA REX
    
    LDI REY, #2       ; button down has been pressed
    SUB REX, REY, REZ
    JPZ ButtonDownPressed

    LDI REY, #1       ; button up has been pressed
    SUB REX, REY, REZ
    JPZ ButtonUpPressed

    _InterruptHandled:
    POP REZ
    POP REY
    POP REX
    RTI

; Whenever the up-button was pressed
ButtonUpPressed:
    PUSH REA

    LDI REA, #1
    ADD REQ, REA

    POP REA    
    JP _InterruptHandled

; Whenever the down-button was pressed
ButtonDownPressed:
    PUSH REA

    LDI REA, #1
    SUB REQ, REA

    POP REA
    JP _InterruptHandled
