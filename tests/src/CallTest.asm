.Code
SET_SP #0x8000

CALL FirstLabel
CALL SecondLabel

HALT

.CallSegment
FirstLabel:
    LDI REA, #0x123
    RTS

SecondLabel:
    LDI REA, #0x456
    RTS

