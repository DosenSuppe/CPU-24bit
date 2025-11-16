# Imports

D-Asm allows developers to import code from other assembly files.
This helps debugging problems and keeping your project organised.

## Syntax
`!IMPORT "path/to/file.asm" as Alias`

## Example


main.asm:
<pre>
!IMPORT "Math.asm" as Math

.Code
LDI REA, #9     ; loading a value into REA
CALL Math.SQRT  ; calling Math.SQRT

HALT
</pre>

----
Math.asm: 
<pre>
.MathLib

; calculates the square root of whatever value is in REA
SQRT:
    [...] ; preserve registers that are going to be modified

    ; Initial guess: REB = REA
    MOV REB, REA      

    ; Iteration count = 5
    LDI REY, 5        

    SQRT_LOOP:
        ; REC = REA / REB
        DIV REA, REB, REC     

        ; REX = REB + REC
        ADD REB, REC, REX     

        ; REX = REX / 2
        LDI REZ, 2            
        DIV REX, REZ          

        ; Update guess: REB = REX
        MOV REB, REX          

        ; Decrement loop counter
        LDI REZ, #1
        SUB REY, REZ          

        ; If REY == 0 -> exit
        JPZ SQRT_DONE          

        ; Otherwise loop again
        JP SQRT_LOOP           

    SQRT_DONE:
        ; Result back into REA
        MOV REA, REB         

        [...] ; restore the registers that have been modified and are non-vital 

        RTS
</pre>

