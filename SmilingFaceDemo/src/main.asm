!IMPORT "./programs/SmileFace.asm" as SmileFace

.Code
SET_SP  $Stack.Start    ; setting up the stack pointer

CALL SmileFace.Main     ; draw smiling face

CALL DisplayDriver.RenderFrame ; render the smiling face

HALT
    
    




