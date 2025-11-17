.DisplayDriver
Render:
    PUSH REX
    PUSH REA
    PUSH REY
    PUSH REZ
    PUSH REQ
    PUSH REB

    LDI REY, #1 ; used for counting offset

    LDI REZ, #0 ; used for end condition
    LDI REQ, #4 ; end of display memory

    LDI REX, DisplayStart
    LDI REA, FrameBuffer

    DisplayRenderLoop:
        LDI REB, [REA] 
        STR [REX], REB

        ADD REX, REY
        ADD REA, REY
        ADD REZ, REY

        SUB REZ, REQ, REB
        JPZ DisplayEnd
        JP DisplayRenderLoop

    DisplayEnd:

    POP REB
    POP REQ
    POP REZ
    POP REY
    POP REA
    POP REX

    RTS

