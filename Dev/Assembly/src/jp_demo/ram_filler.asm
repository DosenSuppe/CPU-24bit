LDI REX, #0xffffff  ; value to fill RAM with
LDI REB, #0xC       ; start address of RAM filling

LDI REA, #1         ; increment value

Loop:     
    STR REB, REX    ; store the value in RAM at address REB

    ADD REA, REB    ; increment address
    MOV REB, ACC    ; move result for next iteration
    JP Loop         ; loop

