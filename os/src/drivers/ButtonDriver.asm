.ButtonDriver
HandleInterrupt:
    ; saving registers
    PUSH REA 
    PUSH REB
    PUSH REX
    PUSH REY

    ; reading the state
    LDI REA, ButtonInterfaceAddress
    LDI REB, [REA]

    ; checking for state (1 = up , 2 = down)
    LDI REX, #0x1
    SUB REB, REX, REY
    JPZ ButtonUpPressed

    LDI REX, #0x2
    SUB REB, REX, REY
    JPZ ButtonDownPressed


    _InterruptHandled:
    ; restoring registers
    POP REY
    POP REX
    POP REB
    POP REA
    
    RTI

; Whenever the up-button was pressed
ButtonUpPressed:

    ; getting display value
    LDI REA, DisplayInterfaceAddress
    LDI REB, #0x1

    LDI REX, [REA]

    ; incrementing display value
    ADD REX, REB

    ; writing back display value
    STR [REA], REX

    JP _InterruptHandled

; Whenever the down-button was pressed
ButtonDownPressed:
    ; getting display value
    LDI REA, DisplayInterfaceAddress
    LDI REB, #0x1

    LDI REX, [REA]

    ; decrementing display value
    SUB REX, REB

    ; writing back display value
    STR [REA], REX

    JP _InterruptHandled
