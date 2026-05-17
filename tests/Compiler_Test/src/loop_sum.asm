; ============================================================
; cc.py output for loop_sum.c
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
    CALL sum
    POP REC                             ; discard arg
    POP REX                             ; restore FP
    RTS

; --- function sum(int n) ---
; frame: 2 local word(s)
sum:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    LDI REA, #0x0
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &total (local)
    STR REY, REA                        ; *target = value
    LDI REA, #0x1
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &i (local)
    STR REY, REA                        ; *target = value
L_sum_loop_0:
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &n (arg)
    LDI REA, [REY]                      ; n
    PUSH REA                            ; save RHS of <=
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_sum_cmp_2
    LDI REA, #1                         ; true
L_sum_cmp_2:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_sum_endloop_1
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &total (local)
    LDI REA, [REY]                      ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &total (local)
    STR REY, REA                        ; *target = value
    LDI REA, #0x1
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    ADD REA, REB
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &i (local)
    STR REY, REA                        ; *target = value
    JP L_sum_loop_0
L_sum_endloop_1:
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &total (local)
    LDI REA, [REY]                      ; total
    POP REC                             ; release local
    POP REC                             ; release local
    POP REX                             ; restore FP
    RTS
