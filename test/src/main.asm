!IMPORT "./drivers/DisplayDriver.asm" as DisplayDriver

.Code
SET_SP Stack
SET_IVR ResetVector

LDI REA, #1
LDI REB, #2
LDI REC, #3

STR [#0x20000], REA
STR [#0x20001], REB
STR [#0x20002], REC

CALL DisplayDriver.Render

.ResetVector
    RTI

HALT


