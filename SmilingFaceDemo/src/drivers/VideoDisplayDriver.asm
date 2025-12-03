.VideoDisplayDriver

@REA: X-Coordinate
@REB: Y-Coordinate
@REC: Color
WritePixel:
    PUSH REN
    PUSH REX

    LDI REN, #4 

    MOV REX, REC    ; adding the color value    (0000 0000 0000 0000 0000 CCCC)

    SHL REX, REN    ; shifting left by 4        (0000 0000 0000 000C CCCC 0000)
    ADD REX, REB    ; adding the Y-Coordinate   (0000 0000 0000 0000 CCCC YYYY)

    SHL REX, REN    ; shifting left by 4        (0000 0000 0000 CCCC YYYY 0000)
    ADD REX, REA    ; adding the X-Coordinate   (0000 0000 0000 CCCC YYYY XXXX)

    LDI REN, $VideoDisplay.Start
    STR [REN], REX  ; storing the value

    POP REX
    POP REN
    RTS

ClearScreen:
    PUSH REX
    PUSH REY

    LDI REX, #0x900000
    LDI REY, $VideoDisplay.Start

    STR [REY], REX

    POP REY
    POP REX
    RTS

    

