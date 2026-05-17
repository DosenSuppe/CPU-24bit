; ============================================================
; cc.py output for add.c
; Auto-generated. Do not edit by hand.
; ============================================================

.Kernel

; Boot stub: set up stack, call main, halt with return value in REA.
    SET_SP $Stack.Start
    SET_IVR $InterruptVector.Start
    CALL main
    HALT

.CCode


; --- function main() ---
; frame: 2 local word(s)
main:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    LDI REA, #0x3
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &x (local)
    STR REY, REA                        ; *target = value
    LDI REA, #0x4
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &y (local)
    STR REY, REA                        ; *target = value
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &y (local)
    LDI REA, [REY]                      ; y
    PUSH REA                            ; arg 1
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &x (local)
    LDI REA, [REY]                      ; x
    PUSH REA                            ; arg 0
    CALL add
    POP REC                             ; discard arg
    POP REC                             ; discard arg
    POP REC                             ; release local
    POP REC                             ; release local
    POP REX                             ; restore FP
    RTS

; --- function add(int a, int b) ---
; frame: 0 local word(s)
add:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    MOV REY, REX
    LDI REZ, #0x4
    ADD REY, REZ                        ; &b (arg)
    LDI REA, [REY]                      ; b
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &a (arg)
    LDI REA, [REY]                      ; a
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REX                             ; restore FP
    RTS
