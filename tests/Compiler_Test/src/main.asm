; Test driver for cc.py. Links a single C translation unit (test_all.c) which
; contains all four example tests as functions. Returning 145 in REA at HALT
; means add / fib / loop_sum / array_test all pass; the per-test results are
; also stored in globals (r_add, r_fib, r_lsum, r_array) in .CData for
; inspection.

!IMPORT "test_all.asm" AS test

.Main

SET_SP $Stack.Start
SET_IVR $InterruptVector.Start

CALL test.main         ; expect REA = 145 (7 + 55 + 55 + 28)

HALT
