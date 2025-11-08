
.Code
LDI REB, #0xE00000
LDI REA, #0x21

STR [REB], REA   ; Store the value in REA to memory address 0xE00000

NOP 
NOP
NOP

LDI REB, [#0xE00000] ; Load the value from memory address 0xE00000 into REB

HALT
