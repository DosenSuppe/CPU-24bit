;.Strings
;@String "Hello, World!" as MyMessagePosition, MyMessageLength ; Define string "Hello, World!" and get its position and length
!import "call_example.asm" as callExample

.Code
LDI SP, #0xf000ff   ; Initialize stack pointer to top of memory

LDI REX, #0x40      ; 0x40 as value of MyMessagePosition

LDI REY, #0x123456

CALL PrintString    ; Call PrintString subroutine

MOV EP0, REY
HALT

PrintString:
    ; set-up
    STR [#0xf00], REY  ; store previous value to be restored later

    LDI REY, #0x00      ; initialize a counter value at 0

    PrintLoop:
        LDI EP0, [REX]                  ; load character into extension port 0
        CALL PrintIncrementCharacter    ; increment string position
        MOV REX, ACC                    ; move new position to REX

        CALL PrintIncrementCounter      ; increment counter
        MOV REY, ACC                    ; move new counter to REY
        MOV REA, ACC                    ; move new counter to A for checking length
        LDI REB, #4                     ; 4 as value of MyMessageLength
        JPZ PrintEnd                    ; end print if all has been read (JPZ needs to be replaced with : CMP REA == REB, PrintEnd )
        JP PrintLoop                    ; continue printing

    PrintIncrementCounter:
        MOV REA, REY    ; move counter to A
        LDI REB, #1
        ADD 
        RTS

    PrintIncrementCharacter:
        MOV REA, REX    ; move string position to A
        LDI REB, #1     ; 1 as increment value
        ADD 
        RTS

    PrintEnd:
        ; Cleaning up and returning
        LDI REY, [#0xf00]   ; restore previous register value
        RTS


