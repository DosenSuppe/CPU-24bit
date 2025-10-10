;   JP instructions jump to labels within a program
;   Once a JP instruction is executed, there is no way to 
;   return to the origin unless programmed otherwise.

.Code               ; Code is placed in the .Code segment in ram (defined in mem.cfg)

LDI REA, 0xffffff   ; loading A and B register with default values
LDI REB, 0x1

ADD                 ; Add them together
JPC MyLabel         ; jump on carry

JumpLabel:          ; this is a label that can be used as a JP or CALL target
    JP EndProgram   ; jump unconditionally to the end

MyLabel:
    MOV REB, REA    ; make A and B equal
    SUB             ; subtract them (result will be 0, so no carry)
    JPZ JumpLabel   ; jump if zero

EndProgram:
    HALT            ; end of program
