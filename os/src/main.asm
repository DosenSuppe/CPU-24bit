
.Code
SETSP #0x20 ; initialize stack pointer
GETSP REB   ; save SP to REB
GETPC REC   ; get the value of this very instruction

HALT
