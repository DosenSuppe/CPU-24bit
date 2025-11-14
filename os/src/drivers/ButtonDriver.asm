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

    LDI REX, #0xE00000
    LDI REZ, #1

    SHL REQ, REZ
    STR [REX], REQ
    
    JP _InterruptHandled

; Whenever the down-button was pressed
ButtonDownPressed:
    LDI REX, #0xE00000
    LDI REZ, #1

    SHR REQ, REZ
    STR [REX], REQ

    JP _InterruptHandled
