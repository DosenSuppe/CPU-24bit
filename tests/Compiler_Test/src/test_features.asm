; ============================================================
; cc.py output for test_features.c
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
; frame: 1 local word(s)
main:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    LDI REA, #0x0
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
    CALL test_inc_dec
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
    LDI REA, #0x5
    LDI REB, #0
    SUB REB, REA, REA                   ; REA = 0 - REA
    PUSH REA                            ; arg 0
    CALL test_ternary
    POP REC                             ; discard arg
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
    CALL test_break_continue
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
    CALL test_string
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
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &total (local)
    LDI REA, [REY]                      ; total
    POP REC                             ; release local
    POP REX                             ; restore FP
    RTS

; --- function test_inc_dec() ---
; frame: 5 local word(s)
test_inc_dec:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    LDI REA, #0x5
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
    MOV REA, REX
    LDI REZ, #0
    SUB REA, REZ                        ; &x (local)
    MOV REY, REA                        ; addr of target
    LDI REA, [REY]                      ; load target
    PUSH REA                            ; save old (postfix result)
    LDI REB, #1
    ADD REA, REB
    STR REY, REA                        ; commit new value
    POP REA                             ; REA = old value
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
    MOV REA, REX
    LDI REZ, #0
    SUB REA, REZ                        ; &x (local)
    MOV REY, REA                        ; addr of target
    LDI REA, [REY]                      ; load target
    LDI REB, #1
    ADD REA, REB
    STR REY, REA                        ; commit new value
    MOV REY, REX
    LDI REZ, #0x2
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
    MOV REA, REX
    LDI REZ, #0
    SUB REA, REZ                        ; &x (local)
    MOV REY, REA                        ; addr of target
    LDI REA, [REY]                      ; load target
    PUSH REA                            ; save old (postfix result)
    LDI REB, #1
    SUB REA, REB
    STR REY, REA                        ; commit new value
    POP REA                             ; REA = old value
    MOV REY, REX
    LDI REZ, #0x3
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
    MOV REA, REX
    LDI REZ, #0
    SUB REA, REZ                        ; &x (local)
    MOV REY, REA                        ; addr of target
    LDI REA, [REY]                      ; load target
    LDI REB, #1
    SUB REA, REB
    STR REY, REA                        ; commit new value
    MOV REY, REX
    LDI REZ, #0x4
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
    MOV REY, REX
    LDI REZ, #0x4
    SUB REY, REZ                        ; &d (local)
    LDI REA, [REY]                      ; d
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0x3
    SUB REY, REZ                        ; &c (local)
    LDI REA, [REY]                      ; c
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0x2
    SUB REY, REZ                        ; &b (local)
    LDI REA, [REY]                      ; b
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &a (local)
    LDI REA, [REY]                      ; a
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REC                             ; release local
    POP REC                             ; release local
    POP REC                             ; release local
    POP REC                             ; release local
    POP REC                             ; release local
    POP REX                             ; restore FP
    RTS

; --- function test_ternary(int n) ---
; frame: 2 local word(s)
test_ternary:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    LDI REA, #0x0
    PUSH REA                            ; save RHS of <
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &n (arg)
    LDI REA, [REY]                      ; n
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_test_ternary_cmp_2
    JP_EQ L_test_ternary_cmp_2
    LDI REA, #1                         ; true
L_test_ternary_cmp_2:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_test_ternary_telse_0
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &n (arg)
    LDI REA, [REY]                      ; n
    LDI REB, #0
    SUB REB, REA, REA                   ; REA = 0 - REA
    JP L_test_ternary_tend_1
L_test_ternary_telse_0:
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &n (arg)
    LDI REA, [REY]                      ; n
L_test_ternary_tend_1:
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
    LDI REA, #0x0
    PUSH REA                            ; save RHS of <
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &n (arg)
    LDI REA, [REY]                      ; n
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_test_ternary_cmp_6
    JP_EQ L_test_ternary_cmp_6
    LDI REA, #1                         ; true
L_test_ternary_cmp_6:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_test_ternary_telse_4
    LDI REA, #0x1
    LDI REB, #0
    SUB REB, REA, REA                   ; REA = 0 - REA
    JP L_test_ternary_tend_5
L_test_ternary_telse_4:
    LDI REA, #0x0
    PUSH REA                            ; save RHS of >
    MOV REY, REX
    LDI REZ, #0x3
    ADD REY, REZ                        ; &n (arg)
    LDI REA, [REY]                      ; n
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_LT L_test_ternary_cmp_10
    JP_EQ L_test_ternary_cmp_10
    LDI REA, #1                         ; true
L_test_ternary_cmp_10:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_test_ternary_telse_8
    LDI REA, #0x1
    JP L_test_ternary_tend_9
L_test_ternary_telse_8:
    LDI REA, #0x0
L_test_ternary_tend_9:
L_test_ternary_tend_5:
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &sign (local)
    LDI REA, [REY]                      ; sign
    PUSH REA                            ; save RHS of *
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &mag (local)
    LDI REA, [REY]                      ; mag
    POP REB                             ; REB = RHS
    MUL REA, REB
    POP REC                             ; release local
    POP REC                             ; release local
    POP REX                             ; restore FP
    RTS

; --- function test_break_continue() ---
; frame: 2 local word(s)
test_break_continue:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    LDI REA, #0x0
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
    LDI REA, #0x0
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
    LDI REA, #0x0
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &local
    STR REY, REA                        ; *local = REA
L_test_break_continue_for_11:
    LDI REY, LIMIT                      ; &LIMIT
    LDI REA, [REY]                      ; LIMIT
    PUSH REA                            ; save RHS of <
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_test_break_continue_cmp_14
    JP_EQ L_test_break_continue_cmp_14
    LDI REA, #1                         ; true
L_test_break_continue_cmp_14:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_test_break_continue_endfor_13
    LDI REA, #0x3
    PUSH REA                            ; save RHS of ==
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_NEQ L_test_break_continue_cmp_18
    LDI REA, #1                         ; true
L_test_break_continue_cmp_18:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_test_break_continue_endif_17
    JP L_test_break_continue_forcont_12 ; continue
L_test_break_continue_endif_17:
    LDI REA, #0x7
    PUSH REA                            ; save RHS of ==
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_NEQ L_test_break_continue_cmp_21
    LDI REA, #1                         ; true
L_test_break_continue_cmp_21:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_test_break_continue_endif_20
    JP L_test_break_continue_endfor_13  ; break
L_test_break_continue_endif_20:
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &sum (local)
    LDI REA, [REY]                      ; sum
    POP REB                             ; REB = RHS
    ADD REA, REB
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &sum (local)
    STR REY, REA                        ; *target = value
L_test_break_continue_forcont_12:
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
    JP L_test_break_continue_for_11
L_test_break_continue_endfor_13:
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &sum (local)
    LDI REA, [REY]                      ; sum
    POP REC                             ; release local
    POP REC                             ; release local
    POP REX                             ; restore FP
    RTS

; --- function test_string() ---
; frame: 9 local word(s)
test_string:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    MOV REY, REX
    LDI REZ, #0x2
    SUB REY, REZ                        ; &buf[0]
    LDI REA, #0x68
    STR REY, REA
    MOV REY, REX
    LDI REZ, #0x1
    SUB REY, REZ                        ; &buf[1]
    LDI REA, #0x69
    STR REY, REA
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &buf[2]
    LDI REA, #0x0
    STR REY, REA
    MOV REY, REX
    LDI REZ, #0x8
    SUB REY, REZ                        ; &pad[0]
    LDI REA, #0x61
    STR REY, REA
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &pad[1]
    LDI REA, #0x62
    STR REY, REA
    MOV REY, REX
    LDI REZ, #0x6
    SUB REY, REZ                        ; &pad[2]
    LDI REA, #0x0
    STR REY, REA
    LDI REA, #0x5
    PUSH REA                            ; save index
    MOV REA, REX
    LDI REZ, #0x8
    SUB REA, REZ                        ; &pad (local)
    POP REB                             ; REB = index
    ADD REA, REB                        ; &base[index]
    MOV REY, REA
    LDI REA, [REY]                      ; deref a[i]
    PUSH REA                            ; save RHS of +
    LDI REA, #0x2
    PUSH REA                            ; save index
    MOV REA, REX
    LDI REZ, #0x8
    SUB REA, REZ                        ; &pad (local)
    POP REB                             ; REB = index
    ADD REA, REB                        ; &base[index]
    MOV REY, REA
    LDI REA, [REY]                      ; deref a[i]
    PUSH REA                            ; save RHS of +
    LDI REA, #0x1
    PUSH REA                            ; save index
    MOV REA, REX
    LDI REZ, #0x8
    SUB REA, REZ                        ; &pad (local)
    POP REB                             ; REB = index
    ADD REA, REB                        ; &base[index]
    MOV REY, REA
    LDI REA, [REY]                      ; deref a[i]
    PUSH REA                            ; save RHS of +
    LDI REA, #0x0
    PUSH REA                            ; save index
    MOV REA, REX
    LDI REZ, #0x8
    SUB REA, REZ                        ; &pad (local)
    POP REB                             ; REB = index
    ADD REA, REB                        ; &base[index]
    MOV REY, REA
    LDI REA, [REY]                      ; deref a[i]
    PUSH REA                            ; save RHS of +
    LDI REA, #0x1
    PUSH REA                            ; save index
    MOV REA, REX
    LDI REZ, #0x2
    SUB REA, REZ                        ; &buf (local)
    POP REB                             ; REB = index
    ADD REA, REB                        ; &base[index]
    MOV REY, REA
    LDI REA, [REY]                      ; deref a[i]
    PUSH REA                            ; save RHS of +
    LDI REA, #0x0
    PUSH REA                            ; save index
    MOV REA, REX
    LDI REZ, #0x2
    SUB REA, REZ                        ; &buf (local)
    POP REB                             ; REB = index
    ADD REA, REB                        ; &base[index]
    MOV REY, REA
    LDI REA, [REY]                      ; deref a[i]
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REC                             ; release local
    POP REC                             ; release local
    POP REC                             ; release local
    POP REC                             ; release local
    POP REC                             ; release local
    POP REC                             ; release local
    POP REC                             ; release local
    POP REC                             ; release local
    POP REC                             ; release local
    POP REX                             ; restore FP
    RTS

.CData

LIMIT:
    DW #0xA                             ; const int
