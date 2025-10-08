; Test program for the segment display

LDI REA, #1 ; initial value to be shifted
LDI REB, #1 ; number of bits to shift to left

Start:
    SHL ; shifting left
    ; Since I am using REA and REB, the SHL does not need any operands
    ; The assembler will automatically use REA and REB for the SHL instruction

    MOV REA, ACC ; moving value for next iteration
    MOV EP0, ACC ; Exposing the result to the port

    JP Start

HALT
