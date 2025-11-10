.ButtonDriver
HandleInterrupt:
    PUSH REA
    PUSH REB
    PUSH REX
    
    LDI REB, #1
    LDI REX, #0xE00000

    LDI REA, [REX]
    ADD REA, REB
    STR [REX], REA

    POP REX
    POP REB
    POP REA 
    RTS

