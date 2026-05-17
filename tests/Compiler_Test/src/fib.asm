; ============================================================
; cc.py output for fib.c
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
; frame: 0 local word(s)
main:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    LDI REA, #0xA
    PUSH REA                            ; arg 0
    CALL fib
    POP REC                             ; discard arg
    POP REX                             ; restore FP
    RTS

; --- function fib(int n) ---
; frame: 0 local word(s)
fib:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    LDI REA, #0x2
    PUSH REA                            ; save RHS of <
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &n (arg)
    LDI REA, [REY]                      ; n
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_fib_cmp_2
    JP_EQ L_fib_cmp_2
    LDI REA, #1                         ; true
L_fib_cmp_2:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_fib_endif_1
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &n (arg)
    LDI REA, [REY]                      ; n
    POP REX                             ; restore FP
    RTS
L_fib_endif_1:
    LDI REA, #0x2
    PUSH REA                            ; save RHS of -
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &n (arg)
    LDI REA, [REY]                      ; n
    POP REB                             ; REB = RHS
    SUB REA, REB
    PUSH REA                            ; arg 0
    CALL fib
    POP REC                             ; discard arg
    PUSH REA                            ; save RHS of +
    LDI REA, #0x1
    PUSH REA                            ; save RHS of -
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &n (arg)
    LDI REA, [REY]                      ; n
    POP REB                             ; REB = RHS
    SUB REA, REB
    PUSH REA                            ; arg 0
    CALL fib
    POP REC                             ; discard arg
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REX                             ; restore FP
    RTS
