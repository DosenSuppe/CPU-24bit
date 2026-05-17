; ============================================================
; cc.py output for test_all.c
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
    LDI REA, #0x4
    PUSH REA                            ; arg 1
    LDI REA, #0x3
    PUSH REA                            ; arg 0
    CALL add
    POP REC                             ; discard arg
    POP REC                             ; discard arg
    LDI REY, r_add                      ; &r_add (global)
    STR REY, REA                        ; *target = value
    LDI REA, #0xA
    PUSH REA                            ; arg 0
    CALL fib
    POP REC                             ; discard arg
    LDI REY, r_fib                      ; &r_fib (global)
    STR REY, REA                        ; *target = value
    LDI REA, #0xA
    PUSH REA                            ; arg 0
    CALL loop_sum
    POP REC                             ; discard arg
    LDI REY, r_lsum                     ; &r_lsum (global)
    STR REY, REA                        ; *target = value
    CALL array_test
    LDI REY, r_array                    ; &r_array (global)
    STR REY, REA                        ; *target = value
    LDI REY, r_array                    ; &r_array
    LDI REA, [REY]                      ; r_array
    PUSH REA                            ; save RHS of +
    LDI REY, r_lsum                     ; &r_lsum
    LDI REA, [REY]                      ; r_lsum
    PUSH REA                            ; save RHS of +
    LDI REY, r_fib                      ; &r_fib
    LDI REA, [REY]                      ; r_fib
    PUSH REA                            ; save RHS of +
    LDI REY, r_add                      ; &r_add
    LDI REA, [REY]                      ; r_add
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REB                             ; REB = RHS
    ADD REA, REB
    POP REB                             ; REB = RHS
    ADD REA, REB
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

; --- function loop_sum(int n) ---
; frame: 2 local word(s)
loop_sum:
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
L_loop_sum_loop_4:
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
    JP_GT L_loop_sum_cmp_6
    LDI REA, #1                         ; true
L_loop_sum_cmp_6:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_loop_sum_endloop_5
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
    JP L_loop_sum_loop_4
L_loop_sum_endloop_5:
    MOV REY, REX
    LDI REZ, #0
    SUB REY, REZ                        ; &total (local)
    LDI REA, [REY]                      ; total
    POP REC                             ; release local
    POP REC                             ; release local
    POP REX                             ; restore FP
    RTS

; --- function array_test() ---
; frame: 9 local word(s)
array_test:
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
    LDI REA, #0x0
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    STR REY, REA                        ; *target = value
L_array_test_loop_7:
    LDI REA, #0x7
    PUSH REA                            ; save RHS of <
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_array_test_cmp_9
    JP_EQ L_array_test_cmp_9
    LDI REA, #1                         ; true
L_array_test_cmp_9:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_array_test_endloop_8
    LDI REA, #0x1
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    ADD REA, REB
    PUSH REA                            ; save value
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    PUSH REA                            ; save index
    MOV REA, REX
    LDI REZ, #0x6
    SUB REA, REZ                        ; &a (local)
    POP REB                             ; REB = index
    ADD REA, REB                        ; &base[index]
    MOV REY, REA                        ; REY = &target
    POP REA                             ; restore value
    STR REY, REA                        ; *target = value
    LDI REA, #0x1
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    ADD REA, REB
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    STR REY, REA                        ; *target = value
    JP L_array_test_loop_7
L_array_test_endloop_8:
    LDI REA, #0x0
    MOV REY, REX
    LDI REZ, #0x8
    SUB REY, REZ                        ; &total (local)
    STR REY, REA                        ; *target = value
    LDI REA, #0x0
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    STR REY, REA                        ; *target = value
L_array_test_loop_11:
    LDI REA, #0x7
    PUSH REA                            ; save RHS of <
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_array_test_cmp_13
    JP_EQ L_array_test_cmp_13
    LDI REA, #1                         ; true
L_array_test_cmp_13:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_array_test_endloop_12
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    PUSH REA                            ; save index
    MOV REA, REX
    LDI REZ, #0x6
    SUB REA, REZ                        ; &a (local)
    POP REB                             ; REB = index
    ADD REA, REB                        ; &base[index]
    MOV REY, REA
    LDI REA, [REY]                      ; deref a[i]
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0x8
    SUB REY, REZ                        ; &total (local)
    LDI REA, [REY]                      ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    MOV REY, REX
    LDI REZ, #0x8
    SUB REY, REZ                        ; &total (local)
    STR REY, REA                        ; *target = value
    LDI REA, #0x1
    PUSH REA                            ; save RHS of +
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    ADD REA, REB
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    STR REY, REA                        ; *target = value
    JP L_array_test_loop_11
L_array_test_endloop_12:
    MOV REY, REX
    LDI REZ, #0x8
    SUB REY, REZ                        ; &total (local)
    LDI REA, [REY]                      ; total
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

r_add:
    DW #0                               ; int
r_fib:
    DW #0                               ; int
r_lsum:
    DW #0                               ; int
r_array:
    DW #0                               ; int
