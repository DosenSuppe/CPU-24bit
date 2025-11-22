!IMPORT "../drivers/DisplayDriver.asm" as DisplayDriver

.SmileFaceProgram

Main:
    PUSH REA 
    PUSH REB

    ; Setting up eyes
    LDI REA, #1
    LDI REB, #6
    SHL REA, REB

    LDI REB, #5
    CALL DisplayDriver.DrawColumn   ; Drawing left eye

    LDI REB, #10
    CALL DisplayDriver.DrawColumn   ; Drawing right eye


    ; Setting up mouth
    LDI REA, #1
    LDI REB, #4
    SHL REA, REB
    CALL DisplayDriver.DrawColumn

    LDI REB, #1
    SHR REA, REB
    LDI REB, #5
    CALL DisplayDriver.DrawColumn
    LDI REB, #6
    CALL DisplayDriver.DrawColumn
    LDI REB, #7
    CALL DisplayDriver.DrawColumn
    LDI REB, #8
    CALL DisplayDriver.DrawColumn
    LDI REB, #9
    CALL DisplayDriver.DrawColumn
    LDI REB, #10
    CALL DisplayDriver.DrawColumn

    LDI REA, #1
    LDI REB, #4
    SHL REA, REB
    LDI REB, #11
    CALL DisplayDriver.DrawColumn

    POP REB
    POP REA     
    RTS
