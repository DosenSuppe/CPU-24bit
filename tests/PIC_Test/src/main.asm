.Prog
Init:
    SET_IVR $InterruptHandler.Start
    SET_SP $Stack.Start

Prog:   ; Keeps the CPU running until an interrupt occurs
    NOP
    JP Prog

.InterruptHandler
GET_INT_ID REA
LDI REX, $MemDevice1.Start  ; load address of device 1
LDI REB, [REX]              ; read value from device 1
LDI REY, #0x100001
LDI REZ, #0x100002
STR REY, REX        ; send "Clear Screen" signal to TTY-Terminal
STR REZ, REB        ; send "Write Character" signal to TTY-Terminal
RTI


