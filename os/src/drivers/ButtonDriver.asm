.ButtonDriver
HandleInterrupt:
    PUSH REX
    PUSH REA

    GET_INT_DATA REX
    
    LDI REA, #0x1FF01 ; saves last button state
    STR [REA], REX

    POP REA
    POP REX
    RTI

