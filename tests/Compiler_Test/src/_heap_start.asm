; _heap_start — return the heap-region start address in REA.
;
; C declares this as `extern int *_heap_start(void);` so it follows the
; standard cc.py calling convention (no args; return value in REA). The
; body is a single LDI of the linker-resolved $Heap.Start symbol; the
; linker patches the address in at link time.
;
; This lives in its own .asm file (not heap.c) because cc.py has no syntax
; for referencing memory-config symbols directly from C source. Kept as a
; leaf function: no FP setup, no locals, no stack adjustments.

.CCode

_heap_start:
    LDI REA, $Heap.Start
    RTS
