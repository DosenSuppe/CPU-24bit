.Prog
Init:
    SET_IVR $InterruptHandler.Start
    SET_SP $Stack.Start

Prog:   ; Keeps the CPU running until an interrupt occurs
    NOP
    JP Prog

.InterruptHandler
LDI REX, $MemDevice1.Start  ; load address of device 1
LDI REB, [REX]              ; read value from device 1

; 0x100001 = ClearScreen
; 0x100002 = WriteCharacter
LDI REZ, #0x100002  ; load memory addresses into registers first. STR [#0x100002], <VALUE> does not currently work for some reason.
STR REZ, REB        ; send "Write Character" signal to TTY-Terminal

RTI


