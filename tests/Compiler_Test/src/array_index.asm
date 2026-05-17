; ============================================================
; cc.py output for array_index.c
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
; frame: 9 local word(s)
main:
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
L_main_loop_0:
    LDI REA, #0x7
    PUSH REA                            ; save RHS of <
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_main_cmp_2
    JP_EQ L_main_cmp_2
    LDI REA, #1                         ; true
L_main_cmp_2:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_main_endloop_1
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
    JP L_main_loop_0
L_main_endloop_1:
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
L_main_loop_4:
    LDI REA, #0x7
    PUSH REA                            ; save RHS of <
    MOV REY, REX
    LDI REZ, #0x7
    SUB REY, REZ                        ; &i (local)
    LDI REA, [REY]                      ; i
    POP REB                             ; REB = RHS
    CMP REA, REB
    LDI REA, #0                         ; default false
    JP_GT L_main_cmp_6
    JP_EQ L_main_cmp_6
    LDI REA, #1                         ; true
L_main_cmp_6:
    LDI REB, #0
    CMP REA, REB
    JP_EQ L_main_endloop_5
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
    JP L_main_loop_4
L_main_endloop_5:
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
