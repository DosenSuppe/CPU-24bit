; ============================================================
; cc.py output for test_heap.c
; Auto-generated. Do not edit by hand.
; ============================================================
!IMPORT "heap.asm"
!IMPORT "_heap_start.asm"

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
    STR_LOC REA, #0x0                   ; *local = REA
    CALL test_sizeof
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    CALL test_casts
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    CALL test_linked_heap
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    CALL test_heap_array
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    LDI REA, #0x97
    PUSH REA                            ; save RHS of -
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    SUB REA, REB
    SET_SP_R REX                        ; SP = FP (release 1 local word(s))
    POP REX                             ; restore FP
    RTS

; --- function test_sizeof() ---
; frame: 4 local word(s)
test_sizeof:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    LDI REA, #0x0
    STR_LOC REA, #0x0                   ; *local = REA
    LDI REA, #0x1                       ; sizeof = 1
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    LDI REA, #0x1                       ; sizeof = 1
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    LDI REA, #0x1                       ; sizeof = 1
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    LDI REA, #0x2                       ; sizeof = 2
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    LDI REA, #0x1                       ; sizeof = 1
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    LDI REA, #0x1                       ; sizeof = 1
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    LDI REA, #0x1                       ; sizeof = 1
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    LDI REA, #0x2                       ; sizeof = 2
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    LDI REA, #0x1                       ; sizeof = 1
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x0                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x0                   ; total = value
    LDR_LOC REA, #0x0                   ; total
    SET_SP_R REX                        ; SP = FP (release 4 local word(s))
    POP REX                             ; restore FP
    RTS

; --- function test_casts() ---
; frame: 4 local word(s)
test_casts:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    LDI REA, #0x7
    STR_LOC REA, #0x0                   ; *local = REA
    MOV REA, REX
    LDI REZ, #0
    SUB REA, REZ                        ; &x (local)
    STR_LOC REA, #0x1                   ; *local = REA
    LDR_LOC REA, #0x1                   ; p
    STR_LOC REA, #0x2                   ; *local = REA
    LDR_LOC REA, #0x2                   ; cp
    STR_LOC REA, #0x3                   ; *local = REA
    LDI REA, #0x2A
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x3                   ; back
    MOV REY, REA
    LDI REA, [REY]                      ; *p
    POP REB                             ; REB = RHS
    ADD REA, REB
    SET_SP_R REX                        ; SP = FP (release 4 local word(s))
    POP REX                             ; restore FP
    RTS

; --- function test_linked_heap() ---
; frame: 3 local word(s)
test_linked_heap:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    LDI REA, #0x2                       ; sizeof = 2
    PUSH REA                            ; arg 0
    CALL malloc
    POP REC                             ; discard arg
    STR_LOC REA, #0x0                   ; head = value
    LDI REA, #0x1
    PUSH REA                            ; save value
    LDR_LOC REA, #0x0                   ; head
    MOV REY, REA                        ; REY = &target
    POP REA                             ; restore value
    STR REY, REA                        ; *target = value
    LDI REA, #0x2                       ; sizeof = 2
    PUSH REA                            ; arg 0
    CALL malloc
    POP REC                             ; discard arg
    PUSH REA                            ; save value
    LDR_LOC REA, #0x0                   ; head
    LDI REB, #0x1
    ADD REA, REB                        ; &.next (+1)
    MOV REY, REA                        ; REY = &target
    POP REA                             ; restore value
    STR REY, REA                        ; *target = value
    LDI REA, #0x2
    PUSH REA                            ; save value
    LDR_LOC REA, #0x0                   ; head
    LDI REB, #0x1
    ADD REA, REB                        ; &.next (+1)
    MOV REY, REA
    LDI REA, [REY]                      ; .next
    MOV REY, REA                        ; REY = &target
    POP REA                             ; restore value
    STR REY, REA                        ; *target = value
    LDI REA, #0x2                       ; sizeof = 2
    PUSH REA                            ; arg 0
    CALL malloc
    POP REC                             ; discard arg
    PUSH REA                            ; save value
    LDR_LOC REA, #0x0                   ; head
    LDI REB, #0x1
    ADD REA, REB                        ; &.next (+1)
    MOV REY, REA
    LDI REA, [REY]                      ; .next
    LDI REB, #0x1
    ADD REA, REB                        ; &.next (+1)
    MOV REY, REA                        ; REY = &target
    POP REA                             ; restore value
    STR REY, REA                        ; *target = value
    LDI REA, #0x3
    PUSH REA                            ; save value
    LDR_LOC REA, #0x0                   ; head
    LDI REB, #0x1
    ADD REA, REB                        ; &.next (+1)
    MOV REY, REA
    LDI REA, [REY]                      ; .next
    LDI REB, #0x1
    ADD REA, REB                        ; &.next (+1)
    MOV REY, REA
    LDI REA, [REY]                      ; .next
    MOV REY, REA                        ; REY = &target
    POP REA                             ; restore value
    STR REY, REA                        ; *target = value
    LDI REA, #0x0
    PUSH REA                            ; save value
    LDR_LOC REA, #0x0                   ; head
    LDI REB, #0x1
    ADD REA, REB                        ; &.next (+1)
    MOV REY, REA
    LDI REA, [REY]                      ; .next
    LDI REB, #0x1
    ADD REA, REB                        ; &.next (+1)
    MOV REY, REA
    LDI REA, [REY]                      ; .next
    LDI REB, #0x1
    ADD REA, REB                        ; &.next (+1)
    MOV REY, REA                        ; REY = &target
    POP REA                             ; restore value
    STR REY, REA                        ; *target = value
    LDI REA, #0x0
    STR_LOC REA, #0x2                   ; *local = REA
    LDR_LOC REA, #0x0                   ; head
    STR_LOC REA, #0x1                   ; cur = value
L_test_linked_heap_loop_0:
    LDI REA, #0x0
    PUSH REA                            ; save RHS of !=
    LDR_LOC REA, #0x1                   ; cur
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_EQ L_test_linked_heap_cmp_2
    LDI REA, #1                         ; true
L_test_linked_heap_cmp_2:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_test_linked_heap_endloop_1
    LDR_LOC REA, #0x1                   ; cur
    MOV REY, REA
    LDI REA, [REY]                      ; .val
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x2                   ; total
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x2                   ; total = value
    LDR_LOC REA, #0x1                   ; cur
    LDI REB, #0x1
    ADD REA, REB                        ; &.next (+1)
    MOV REY, REA
    LDI REA, [REY]                      ; .next
    STR_LOC REA, #0x1                   ; cur = value
    JP L_test_linked_heap_loop_0
L_test_linked_heap_endloop_1:
    LDR_LOC REA, #0x0                   ; head
    PUSH REA                            ; arg 0
    CALL free
    POP REC                             ; discard arg
    LDR_LOC REA, #0x2                   ; total
    SET_SP_R REX                        ; SP = FP (release 3 local word(s))
    POP REX                             ; restore FP
    RTS

; --- function test_heap_array() ---
; frame: 4 local word(s)
test_heap_array:
    PUSH REX                            ; save old FP
    GET_SP REX                          ; FP = SP
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    PUSH #0                             ; reserve local
    LDI REA, #0xA
    STR_LOC REA, #0x0                   ; *local = REA
    LDR_LOC REA, #0x0                   ; n
    PUSH REA                            ; save RHS of *
    LDI REA, #0x1                       ; sizeof = 1
    POP REB                             ; REB = RHS
    MUL REA, REB
    PUSH REA                            ; arg 0
    CALL malloc
    POP REC                             ; discard arg
    STR_LOC REA, #0x1                   ; *local = REA
    LDI REA, #0x0
    STR_LOC REA, #0x2                   ; i = value
L_test_heap_array_for_3:
    LDR_LOC REA, #0x0                   ; n
    PUSH REA                            ; save RHS of <
    LDR_LOC REA, #0x2                   ; i
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_test_heap_array_cmp_6
    JP_EQ L_test_heap_array_cmp_6
    LDI REA, #1                         ; true
L_test_heap_array_cmp_6:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_test_heap_array_endfor_5
    LDR_LOC REA, #0x2                   ; i
    PUSH REA                            ; save RHS of *
    LDR_LOC REA, #0x2                   ; i
    POP REB                             ; REB = RHS
    MUL REA, REB
    PUSH REA                            ; save value
    LDR_LOC REA, #0x2                   ; i
    PUSH REA                            ; save scaled index
    LDR_LOC REA, #0x1                   ; arr
    POP REB                             ; REB = scaled index
    ADD REA, REB                        ; &base[index]
    MOV REY, REA                        ; REY = &target
    POP REA                             ; restore value
    STR REY, REA                        ; *target = value
L_test_heap_array_forcont_4:
    MOV REA, REX
    LDI REZ, #0x2
    SUB REA, REZ                        ; &i (local)
    MOV REY, REA                        ; addr of target
    LDI REA, [REY]                      ; load target
    PUSH REA                            ; save old (postfix result)
    LDI REB, #1
    ADD REA, REB
    STR REY, REA                        ; commit new value
    POP REA                             ; REA = old value
    JP L_test_heap_array_for_3
L_test_heap_array_endfor_5:
    LDI REA, #0x0
    STR_LOC REA, #0x3                   ; *local = REA
    LDI REA, #0x0
    STR_LOC REA, #0x2                   ; i = value
L_test_heap_array_for_8:
    LDR_LOC REA, #0x0                   ; n
    PUSH REA                            ; save RHS of <
    LDR_LOC REA, #0x2                   ; i
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_test_heap_array_cmp_11
    JP_EQ L_test_heap_array_cmp_11
    LDI REA, #1                         ; true
L_test_heap_array_cmp_11:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_test_heap_array_endfor_10
    LDR_LOC REA, #0x2                   ; i
    PUSH REA                            ; save scaled index
    LDR_LOC REA, #0x1                   ; arr
    POP REB                             ; REB = scaled index
    ADD REA, REB                        ; &base[index]
    MOV REY, REA
    LDI REA, [REY]                      ; deref a[i]
    PUSH REA                            ; save RHS of +
    LDR_LOC REA, #0x3                   ; sum
    POP REB                             ; REB = RHS
    ADD REA, REB
    STR_LOC REA, #0x3                   ; sum = value
L_test_heap_array_forcont_9:
    MOV REA, REX
    LDI REZ, #0x2
    SUB REA, REZ                        ; &i (local)
    MOV REY, REA                        ; addr of target
    LDI REA, [REY]                      ; load target
    PUSH REA                            ; save old (postfix result)
    LDI REB, #1
    ADD REA, REB
    STR REY, REA                        ; commit new value
    POP REA                             ; REA = old value
    JP L_test_heap_array_for_8
L_test_heap_array_endfor_10:
    LDR_LOC REA, #0x3                   ; sum
    SET_SP_R REX                        ; SP = FP (release 4 local word(s))
    POP REX                             ; restore FP
    RTS
