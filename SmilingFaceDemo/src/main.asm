;!IMPORT "./programs/SmileFace.asm" as SmileFace
!IMPORT "./drivers/VideoDisplayDriver.asm" as VideoDisplayDriver

.Code
SET_SP  $Stack.Start    ; setting up the stack pointer

;CALL SmileFace.Main     ; draw smiling face
;CALL DisplayDriver.RenderFrame ; render the smiling face

CALL VideoDisplayDriver.ClearScreen

LDI REA, #10
LDI REB, #10
LDI REC, #0b

CALL VideoDisplayDriver.WritePixel

HALT
    
    




