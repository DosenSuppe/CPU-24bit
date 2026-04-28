.Prog

LDI REA, #0x01
LDI REB, #0x02

CMP REA, REB
CALL_EQ EqualTo
CALL_LT LessThan
CALL_GT GreaterThan

HALT

EqualTo:
    LDI REZ, #1
    RTS

LessThan:
    LDI REZ, #2
    RTS

GreaterThan:
    LDI REZ, #3
    RTS