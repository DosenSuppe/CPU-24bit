LDI EP0, #0x5   ; 0x5 is the precalculated address of instruction in line 6
JP EP0          ; Jump to line 6
NOP
NOP

LDI REX, #0xA   ; 0xA is the precalculated address of instruction in line 11
JP REX          ; Jump to line 11
NOP
NOP

HALT            ; End of program

