; The CALL instruction acts similar to the JP instruction
; but it also saves the return address on the stack
; allowing the program to return to the instruction
.Code

LDI SP, #0xf000ff   ; Initialize stack pointer to top of memory

LDI REA, #5         ; Load A-Register with 5
LDI REB, #1         ; Load B-Register with 1

CountDown:
    CALL MySUB
    JPZ EndProgram  ; If A is zero, end program

    MOV REA, ACC    ; Move result back to A
    JP CountDown    ; Repeat

MySUB:
    SUB             ; Subtract B from A
    RTS             ; return from subroutine

EndProgram:
    HALT
