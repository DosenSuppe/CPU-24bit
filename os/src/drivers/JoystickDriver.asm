.JoystickDriver
HandleInterrupt:
    PUSH REA
    PUSH REB
    PUSH REX
    PUSH REY

    LDI REA, #0xE00000  ; address of joystick data register
    LDI REB, #0xE00001  ; second joystick register (contains data forwarded through REA)
    
    LDI REX, [REA]
    LDI REY, [REB]

    SUB REX, REY
    JPZ End ; when zero, no change

    STR [REB], REY

    JP End

End:
    POP REY
    POP REX
    POP REB
    POP REA
    RTI
